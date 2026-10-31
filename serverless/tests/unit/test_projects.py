import pytest

BENCH = {"name": "garden bench", "description": "for the backyard"}
STORAGE_ATTRIBUTES = {"PK", "SK", "GSI1PK", "GSI1SK", "entity"}


def stored(table, project_id):
    """The raw record in the fake table, exactly as DynamoDB holds it."""
    return table.get_item(Key={"PK": "MAKER#m-test", "SK": f"PROJECT#{project_id}"})["Item"]


def create_projects(api, count):
    return [api("POST", "/projects", {"name": f"project {i}"})[1]["project_id"] for i in range(count)]


def set_status(table, project_id, status):
    """Change a project's status directly in the table (the status route comes in Part B step 2)."""
    table.update_item(
        Key={"PK": "MAKER#m-test", "SK": f"PROJECT#{project_id}"},
        UpdateExpression="SET #status = :status",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":status": status},
    )


# --- POST /projects ---

def test_create_returns_201_as_a_draft(table, api):
    status, project = api("POST", "/projects", BENCH)

    assert status == 201
    assert project["name"] == "garden bench"
    assert project["description"] == "for the backyard"
    assert project["status"] == "draft"
    assert project["version"] == 1
    assert "published_at" not in project
    assert not STORAGE_ATTRIBUTES & set(project)


def test_create_starts_the_project_collection_on_gsi1(table, api):
    _, project = api("POST", "/projects", BENCH)

    record = stored(table, project["project_id"])
    assert record["GSI1PK"] == f"PROJECT#{project['project_id']}"
    assert record["GSI1SK"] == "PROJECT"
    assert record["entity"] == "project"


def test_create_defaults_description_to_empty(table, api):
    _, project = api("POST", "/projects", {"name": "shelf"})

    assert project["description"] == ""


@pytest.mark.parametrize(
    "body, message",
    [
        ({}, "name is required"),
        ({"name": "  "}, "name is required"),
        ({"name": "x", "description": 5}, "description must be text"),
        ({"name": "x", "status": "finished"}, "unknown fields: status"),
        ({"name": "x", "type": "lumber"}, "unknown fields: type"),
        ({"name": "x", "PK": "MAKER#someone-else"}, "unknown fields: PK"),
        ("{oops", "body must be valid JSON"),
    ],
)
def test_create_rejects_bad_input(table, api, body, message):
    status, error = api("POST", "/projects", body)

    assert status == 400
    assert message in error["message"]
    assert table.scan()["Count"] == 0


# --- GET /projects/<project_id> ---

def test_get_returns_the_created_project(table, api):
    _, created = api("POST", "/projects", BENCH)

    status, project = api("GET", f"/projects/{created['project_id']}")

    assert status == 200
    assert project == created


def test_get_missing_project_returns_404(table, api):
    status, error = api("GET", "/projects/does-not-exist")

    assert status == 404
    assert error["message"] == "project not found"


# --- GET /projects ---

def test_list_pages_newest_first_until_no_cursor(table, api):
    created = create_projects(api, 13)

    pages, cursor = [], None
    while True:
        query = {"limit": "5"} | ({"cursor": cursor} if cursor else {})
        status, page = api("GET", "/projects", query=query)
        assert status == 200
        pages.append([project["project_id"] for project in page["projects"]])
        cursor = page["next_cursor"]
        if cursor is None:
            break

    assert [len(page) for page in pages] == [5, 5, 3]
    assert [project_id for page in pages for project_id in page] == list(reversed(created))


def test_list_returns_only_projects(table, api):
    api("POST", "/projects", BENCH)
    api("POST", "/items", {"name": "oak plank", "type": "lumber"})

    _, page = api("GET", "/projects")

    assert [project["name"] for project in page["projects"]] == ["garden bench"]


def test_list_filters_by_status(table, api):
    draft_id, started_id, other_draft_id = create_projects(api, 3)
    set_status(table, started_id, "in_progress")

    _, started = api("GET", "/projects", query={"status": "in_progress"})
    _, drafts = api("GET", "/projects", query={"status": "draft"})

    assert [project["project_id"] for project in started["projects"]] == [started_id]
    assert [project["project_id"] for project in drafts["projects"]] == [other_draft_id, draft_id]


def test_list_rejects_unknown_status(table, api):
    status, _ = api("GET", "/projects", query={"status": "done"})

    assert status == 400


def test_list_rejects_a_cursor_from_the_items_list(table, api):
    for i in range(3):
        api("POST", "/items", {"name": f"board {i}", "type": "lumber"})
    _, item_page = api("GET", "/items", query={"limit": "1"})

    status, error = api("GET", "/projects", query={"cursor": item_page["next_cursor"]})

    assert status == 400
    assert error["message"] == "cursor is not valid"


# --- PATCH /projects/<project_id> ---

def test_update_changes_fields_and_bumps_version(table, api):
    _, created = api("POST", "/projects", BENCH)

    status, project = api("PATCH", f"/projects/{created['project_id']}", {"name": "big bench"})

    assert status == 200
    assert project["name"] == "big bench"
    assert project["description"] == "for the backyard"
    assert project["version"] == 2
    assert project["status"] == "draft"
    assert stored(table, created["project_id"])["name"] == "big bench"


@pytest.mark.parametrize(
    "body, message",
    [
        ({}, "nothing to update"),
        ({"status": "finished"}, "unknown fields: status"),
        ({"published_at": "2026-01-01"}, "unknown fields: published_at"),
        ({"name": ""}, "name is required"),
    ],
)
def test_update_rejects_bad_input(table, api, body, message):
    _, created = api("POST", "/projects", BENCH)

    status, error = api("PATCH", f"/projects/{created['project_id']}", body)

    assert status == 400
    assert message in error["message"]
    assert stored(table, created["project_id"])["version"] == 1


def test_update_missing_project_returns_404(table, api):
    status, _ = api("PATCH", "/projects/does-not-exist", {"name": "x"})

    assert status == 404


# --- DELETE /projects/<project_id> ---

def test_delete_returns_204_and_removes_the_project(table, api):
    _, created = api("POST", "/projects", BENCH)

    status, body = api("DELETE", f"/projects/{created['project_id']}")

    assert status == 204
    assert body is None
    assert api("GET", f"/projects/{created['project_id']}")[0] == 404


def test_delete_missing_project_returns_404(table, api):
    status, _ = api("DELETE", "/projects/does-not-exist")

    assert status == 404
