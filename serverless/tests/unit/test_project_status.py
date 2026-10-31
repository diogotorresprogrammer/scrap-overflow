import pytest


def stored(table, project_id):
    """The raw record in the fake table, exactly as DynamoDB holds it."""
    return table.get_item(Key={"PK": "MAKER#m-test", "SK": f"PROJECT#{project_id}"})["Item"]


def new_project(api):
    return api("POST", "/projects", {"name": "garden bench"})[1]["project_id"]


def move(api, project_id, status):
    return api("POST", f"/projects/{project_id}/status", {"status": status})


def project_in(api, *path):
    """A new project walked through the given statuses, e.g. project_in(api, "in_progress", "finished")."""
    project_id = new_project(api)
    for status in path:
        assert move(api, project_id, status)[0] == 200
    return project_id


# --- POST /projects/<project_id>/status: allowed moves ---

@pytest.mark.parametrize(
    "path, target",
    [
        ((), "in_progress"),  # start a draft
        ((), "archived"),
        (("in_progress",), "finished"),
        (("in_progress",), "archived"),
        (("in_progress", "finished"), "in_progress"),  # reopen
        (("in_progress", "finished"), "archived"),
    ],
)
def test_allowed_move_returns_the_updated_project(table, api, path, target):
    project_id = project_in(api, *path)

    status, project = move(api, project_id, target)

    assert status == 200
    assert project["status"] == target
    assert project["version"] == len(path) + 2
    assert stored(table, project_id)["status"] == target


def test_finishing_records_finished_at(table, api):
    project_id = project_in(api, "in_progress")

    _, project = move(api, project_id, "finished")

    assert project["finished_at"] == project["modified_at"]


def test_archiving_unpublishes(table, api):
    project_id = project_in(api, "in_progress")
    api("POST", f"/projects/{project_id}/publish")

    _, project = move(api, project_id, "archived")

    assert "published_at" not in project
    assert "published_at" not in stored(table, project_id)


# --- POST /projects/<project_id>/status: refused moves ---

@pytest.mark.parametrize(
    "path, target",
    [
        ((), "finished"),  # a draft can't be finished
        (("in_progress", "finished"), "finished"),
        (("archived",), "in_progress"),  # nothing leaves archived for now
        (("archived",), "archived"),
    ],
)
def test_disallowed_move_returns_409_and_changes_nothing(table, api, path, target):
    project_id = project_in(api, *path)
    before = stored(table, project_id)

    status, error = move(api, project_id, target)

    assert status == 409
    assert before["status"] in error["message"]
    assert stored(table, project_id) == before


@pytest.mark.parametrize(
    "body, message",
    [
        ({"status": "draft"}, "status must be one of"),  # nothing moves back to draft
        ({"status": "done"}, "status must be one of"),
        ({"status": 5}, "status must be one of"),
        ({}, "status must be one of"),
        ({"status": "finished", "name": "x"}, "unknown fields: name"),
        ("{oops", "body must be valid JSON"),
    ],
)
def test_bad_status_request_returns_400(table, api, body, message):
    project_id = new_project(api)

    status, error = api("POST", f"/projects/{project_id}/status", body)

    assert status == 400
    assert message in error["message"]


def test_status_of_missing_project_returns_404(table, api):
    status, _ = move(api, "does-not-exist", "in_progress")

    assert status == 404


def test_status_filter_sees_the_new_status(table, api):
    project_id = project_in(api, "in_progress")

    _, page = api("GET", "/projects", query={"status": "in_progress"})

    assert [project["project_id"] for project in page["projects"]] == [project_id]


# --- POST /projects/<project_id>/publish ---

@pytest.mark.parametrize("path", [("in_progress",), ("in_progress", "finished")])
def test_publish_sets_published_at(table, api, path):
    project_id = project_in(api, *path)

    status, project = api("POST", f"/projects/{project_id}/publish")

    assert status == 200
    assert project["published_at"] == project["modified_at"]


def test_publishing_again_keeps_the_first_date(table, api):
    project_id = project_in(api, "in_progress")
    _, first = api("POST", f"/projects/{project_id}/publish")

    _, again = api("POST", f"/projects/{project_id}/publish")

    assert again["published_at"] == first["published_at"]


@pytest.mark.parametrize("path", [(), ("archived",)])
def test_publish_draft_or_archived_returns_409(table, api, path):
    project_id = project_in(api, *path)

    status, _ = api("POST", f"/projects/{project_id}/publish")

    assert status == 409
    assert "published_at" not in stored(table, project_id)


def test_publish_missing_project_returns_404(table, api):
    status, _ = api("POST", "/projects/does-not-exist/publish")

    assert status == 404


# --- DELETE /projects/<project_id>/publish ---

def test_unpublish_removes_published_at(table, api):
    project_id = project_in(api, "in_progress")
    api("POST", f"/projects/{project_id}/publish")

    status, project = api("DELETE", f"/projects/{project_id}/publish")

    assert status == 200
    assert "published_at" not in project
    assert "published_at" not in stored(table, project_id)


def test_unpublish_when_not_published_is_fine(table, api):
    project_id = new_project(api)

    status, project = api("DELETE", f"/projects/{project_id}/publish")

    assert status == 200
    assert "published_at" not in project


def test_unpublish_missing_project_returns_404(table, api):
    status, _ = api("DELETE", "/projects/does-not-exist/publish")

    assert status == 404
