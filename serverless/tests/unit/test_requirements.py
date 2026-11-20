import pytest

SLAT = {"label": "seat slat", "type": "lumber", "length": 1200, "width": 90, "height": 20}


def new_project(api):
    return api("POST", "/projects", {"name": "garden bench"})[1]["project_id"]


def add(api, project_id, body):
    return api("POST", f"/projects/{project_id}/requirements", body)


def stored(table, requirement_id):
    """The raw record in the fake table, or None."""
    return table.get_item(Key={"PK": "MAKER#m-test", "SK": f"REQ#{requirement_id}"}).get("Item")


def stored_requirements(table):
    return [r for r in table.scan()["Items"] if r["SK"].startswith("REQ#")]


# --- POST /projects/<project_id>/requirements ---

def test_create_one_requirement_by_default(table, api):
    project_id = new_project(api)

    status, body = add(api, project_id, SLAT)

    assert status == 201
    [requirement] = body["requirements"]
    assert requirement["project_id"] == project_id
    assert requirement["label"] == "seat slat"
    assert (requirement["type"], requirement["length"], requirement["width"], requirement["height"]) == ("lumber", 1200, 90, 20)
    assert requirement["version"] == 1
    assert "filled_by" not in requirement
    assert not {"PK", "SK", "GSI1PK", "GSI1SK", "entity"} & set(requirement)


def test_create_puts_requirement_in_the_project_collection(table, api):
    project_id = new_project(api)

    _, body = add(api, project_id, SLAT)

    requirement_id = body["requirements"][0]["requirement_id"]
    record = stored(table, requirement_id)
    assert record["GSI1PK"] == f"PROJECT#{project_id}"
    assert record["GSI1SK"] == f"REQ#{requirement_id}"
    assert record["entity"] == "requirement"


def test_count_creates_that_many_records(table, api):
    project_id = new_project(api)

    status, body = add(api, project_id, SLAT | {"count": 4})

    assert status == 201
    ids = [r["requirement_id"] for r in body["requirements"]]
    assert len(ids) == len(set(ids)) == 4
    assert sorted(r["requirement_id"] for r in stored_requirements(table)) == sorted(ids)
    assert all(r["label"] == "seat slat" and r["length"] == 1200 for r in stored_requirements(table))


def test_count_of_25_fits(table, api):
    project_id = new_project(api)

    status, body = add(api, project_id, SLAT | {"count": 25})

    assert status == 201
    assert len(body["requirements"]) == 25
    assert len(stored_requirements(table)) == 25


def test_only_type_is_required(table, api):
    project_id = new_project(api)

    status, body = add(api, project_id, {"type": "metal"})

    assert status == 201
    [requirement] = body["requirements"]
    assert requirement["label"] == ""
    assert not {"length", "width", "height"} & set(requirement)


@pytest.mark.parametrize(
    "body, message",
    [
        ({"label": "slat"}, "type must be one of"),
        ({"type": "wood"}, "type must be one of"),
        ({"type": "lumber", "length": 12.5}, "length must be a positive whole number"),
        ({"type": "lumber", "width": None}, "width must be a positive whole number"),
        ({"type": "lumber", "label": 3}, "label must be text"),
        ({"type": "lumber", "count": 0}, "count must be a whole number from 1 to 25"),
        ({"type": "lumber", "count": 26}, "count must be a whole number from 1 to 25"),
        ({"type": "lumber", "count": "4"}, "count must be a whole number from 1 to 25"),
        ({"type": "lumber", "count": True}, "count must be a whole number from 1 to 25"),
        ({"type": "lumber", "filled_by": "x"}, "unknown fields: filled_by"),
        ({"type": "lumber", "project_id": "x"}, "unknown fields: project_id"),
        ("{oops", "body must be valid JSON"),
    ],
)
def test_create_rejects_bad_input(table, api, body, message):
    project_id = new_project(api)

    status, error = add(api, project_id, body)

    assert status == 400
    assert message in error["message"]
    assert stored_requirements(table) == []


def test_create_for_missing_project_returns_404_and_writes_nothing(table, api):
    status, error = add(api, "does-not-exist", SLAT | {"count": 3})

    assert status == 404
    assert error["message"] == "project not found"
    assert stored_requirements(table) == []


def test_requirements_stay_out_of_other_lists(table, api):
    project_id = new_project(api)
    add(api, project_id, SLAT | {"count": 3})

    _, projects = api("GET", "/projects")
    _, items = api("GET", "/items")

    assert [p["project_id"] for p in projects["projects"]] == [project_id]
    assert items["items"] == []


# --- DELETE /projects/<project_id>/requirements/<requirement_id> ---

def first_requirement(api, project_id):
    return add(api, project_id, SLAT)[1]["requirements"][0]["requirement_id"]


def test_delete_returns_204_and_removes_it(table, api):
    project_id = new_project(api)
    requirement_id = first_requirement(api, project_id)

    status, body = api("DELETE", f"/projects/{project_id}/requirements/{requirement_id}")

    assert status == 204
    assert body is None
    assert stored(table, requirement_id) is None


def test_delete_missing_requirement_returns_404(table, api):
    project_id = new_project(api)

    status, error = api("DELETE", f"/projects/{project_id}/requirements/does-not-exist")

    assert status == 404
    assert error["message"] == "requirement not found"


def test_delete_through_another_project_returns_404_and_keeps_it(table, api):
    project_id, other_project_id = new_project(api), new_project(api)
    requirement_id = first_requirement(api, project_id)

    status, _ = api("DELETE", f"/projects/{other_project_id}/requirements/{requirement_id}")

    assert status == 404
    assert stored(table, requirement_id) is not None


def test_delete_filled_requirement_returns_409_and_keeps_it(table, api):
    project_id = new_project(api)
    requirement_id = first_requirement(api, project_id)
    table.update_item(  # filling requirements comes in step 5; fake it here
        Key={"PK": "MAKER#m-test", "SK": f"REQ#{requirement_id}"},
        UpdateExpression="SET filled_by = :item",
        ExpressionAttributeValues={":item": "some-item"},
    )

    status, error = api("DELETE", f"/projects/{project_id}/requirements/{requirement_id}")

    assert status == 409
    assert "filled" in error["message"]
    assert stored(table, requirement_id)["filled_by"] == "some-item"
