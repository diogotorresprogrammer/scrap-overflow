import pytest

from api import app as app_module

OAK ={"name": "oak plank", "type": "lumber", "length": 22, "width": 2400, "height": 200}
STORAGE_ATTRIBUTES = {"PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK", "dim_mid", "dim_min", "entity"}


def stored(table, item_id):
    """The raw record in the fake table, exactly as DynamoDB holds it."""
    return table.get_item(Key={"PK": "MAKER#m-test", "SK": f"ITEM#{item_id}"})["Item"]


# --- POST /items ---

def test_create_returns_201_with_public_fields_only(table, api):
    status, item = api("POST", "/items", OAK)

    assert status == 201
    assert item["name"] == "oak plank"
    assert item["state"] == "unassigned"
    assert item["version"] == 1
    assert item["length"] == 22 and isinstance(item["length"], int)
    assert not STORAGE_ATTRIBUTES & set(item)


def test_create_puts_item_with_all_dimensions_on_matching_index(table, api):
    _, item = api("POST", "/items", OAK)

    record = stored(table, item["item_id"])
    assert record["GSI2PK"] == "MAKER#m-test#TYPE#lumber"
    assert (record["GSI2SK"], record["dim_mid"], record["dim_min"]) == (2400, 200, 22)


def test_create_without_dimensions_stays_off_matching_index(table, api):
    _, item = api("POST", "/items", {"name": "old fridge", "type": "appliance"})

    record = stored(table, item["item_id"])
    assert "GSI2PK" not in record
    assert "length" not in record


@pytest.mark.parametrize(
    "body, message",
    [
        ({"type": "lumber"}, "name is required"),
        ({"name": "x", "type": "wood"}, "type must be one of"),
        ({"name": "x", "type": ["lumber"]}, "type must be one of"),
        ({"name": "x", "type": "lumber", "length": 24.5}, "length must be a positive whole number"),
        ({"name": "x", "type": "lumber", "length": True}, "length must be a positive whole number"),
        ({"name": "x", "type": "lumber", "length": 0}, "length must be a positive whole number"),
        ({"name": "x", "type": "lumber", "PK": "MAKER#someone-else"}, "unknown fields: PK"),
        ({"name": "x", "type": "lumber", "state": "used"}, "unknown fields: state"),
        ("{oops", "body must be valid JSON"),
        ("[1, 2]", "body must be a JSON object"),
        (None, "name is required"),
    ],
)
def test_create_rejects_bad_input(table, api, body, message):
    status, error = api("POST", "/items", body)

    assert status == 400
    assert message in error["message"]
    assert table.scan()["Count"] == 0


# --- GET /items/<item_id> ---

def test_get_returns_the_created_item(table, api):
    _, created = api("POST", "/items", OAK)

    status, item = api("GET", f"/items/{created['item_id']}")

    assert status == 200
    assert item == created


def test_get_missing_item_returns_404(table, api):
    status, error = api("GET", "/items/does-not-exist")

    assert status == 404
    assert error["message"] == "item not found"


# --- GET /items ---

def create_items(api, count):
    return [api("POST", "/items", {"name": f"board {i}", "type": "lumber"})[1]["item_id"] for i in range(count)]


def test_list_pages_newest_first_until_no_cursor(table, api):
    created = create_items(api, 25)

    pages, cursor = [], None
    while True:
        query = {"limit": "10"} | ({"cursor": cursor} if cursor else {})
        status, page = api("GET", "/items", query=query)
        assert status == 200
        pages.append([item["item_id"] for item in page["items"]])
        cursor = page["next_cursor"]
        if cursor is None:
            break

    assert [len(page) for page in pages] == [10, 10, 5]
    assert [item_id for page in pages for item_id in page] == list(reversed(created))


def test_list_default_page_size_is_20(table, api):
    create_items(api, 21)

    _, page = api("GET", "/items")

    assert len(page["items"]) == 20
    assert page["next_cursor"] is not None


def test_list_hides_storage_attributes(table, api):
    api("POST", "/items", OAK)

    _, page = api("GET", "/items")

    assert not STORAGE_ATTRIBUTES & set(page["items"][0])


def test_list_returns_only_my_items(table, api):
    api("POST", "/items", OAK)
    table.put_item(Item={"PK": "MAKER#someone-else", "SK": "ITEM#x", "name": "not mine"})
    table.put_item(Item={"PK": "MAKER#m-test", "SK": "PROJECT#p1", "name": "a project, not an item"})

    _, page = api("GET", "/items")

    assert [item["name"] for item in page["items"]] == ["oak plank"]


@pytest.mark.parametrize("limit", ["abc", "0", "101", "2.5"])
def test_list_rejects_bad_limit(table, api, limit):
    status, _ = api("GET", "/items", query={"limit": limit})

    assert status == 400


@pytest.mark.parametrize(
    "cursor",
    [
        "not-base64!!",
        "eyJub3QiOiAianNvbiJ9",  # valid base64 and JSON, wrong keys
        "eyJQSyI6ICJNQUtFUiNzb21lb25lLWVsc2UiLCAiU0siOiAiSVRFTSN4In0",  # another maker's partition
        "eyJQSyI6ICJNQUtFUiNtLXRlc3QiLCAiU0siOiAiUFJPSkVDVCNwMSJ9",  # my partition, but a project
    ],
)
def test_list_rejects_tampered_cursor(table, api, cursor):
    status, error = api("GET", "/items", query={"cursor": cursor})

    assert status == 400
    assert error["message"] == "cursor is not valid"


# --- PATCH /items/<item_id> ---

def test_update_changes_only_sent_fields_and_bumps_version(table, api):
    _, created = api("POST", "/items", OAK)

    status, item = api("PATCH", f"/items/{created['item_id']}", {"name": "pine board"})

    assert status == 200
    assert item["name"] == "pine board"
    assert item["version"] == 2
    assert item["width"] == 2400 and item["type"] == "lumber"
    assert item["modified_at"] >= created["modified_at"]
    assert stored(table, created["item_id"])["name"] == "pine board"


def test_update_recomputes_matching_index(table, api):
    _, created = api("POST", "/items", OAK)

    api("PATCH", f"/items/{created['item_id']}", {"width": 100})

    record = stored(table, created["item_id"])
    assert (record["GSI2SK"], record["dim_mid"], record["dim_min"]) == (200, 100, 22)


def test_update_changing_type_moves_item_on_matching_index(table, api):
    _, created = api("POST", "/items", OAK)

    api("PATCH", f"/items/{created['item_id']}", {"type": "metal"})

    assert stored(table, created["item_id"])["GSI2PK"] == "MAKER#m-test#TYPE#metal"


def test_update_removing_a_dimension_takes_item_off_matching_index(table, api):
    _, created = api("POST", "/items", OAK)

    status, item = api("PATCH", f"/items/{created['item_id']}", {"height": None})

    assert status == 200
    assert "height" not in item
    record = stored(table, created["item_id"])
    assert "height" not in record
    assert not {"GSI2PK", "GSI2SK", "dim_mid", "dim_min"} & set(record)


def test_update_missing_item_returns_404(table, api):
    status, _ = api("PATCH", "/items/does-not-exist", {"name": "x"})

    assert status == 404


@pytest.mark.parametrize(
    "body, message",
    [
        ({}, "nothing to update"),
        ({"PK": "MAKER#someone-else"}, "unknown fields: PK"),
        ({"state": "used"}, "unknown fields: state"),
        ({"name": "  "}, "name is required"),
        ({"length": -1}, "length must be a positive whole number"),
        ("{oops", "body must be valid JSON"),
    ],
)
def test_update_rejects_bad_input(table, api, body, message):
    _, created = api("POST", "/items", OAK)

    status, error = api("PATCH", f"/items/{created['item_id']}", body)

    assert status == 400
    assert message in error["message"]
    assert stored(table, created["item_id"])["version"] == 1


def test_update_with_stale_version_returns_409_and_keeps_the_other_save(table, api, monkeypatch):
    _, created = api("POST", "/items", OAK)
    stale = stored(table, created["item_id"])  # what this request read, at version 1
    api("PATCH", f"/items/{created['item_id']}", {"name": "renamed in another tab"})  # now version 2

    class StaleRead:
        """The table, except get_item returns the old snapshot, as if another save landed in between."""

        def __getattr__(self, name):
            return getattr(table, name)

        def get_item(self, **kwargs):
            return {"Item": dict(stale)}

    monkeypatch.setattr(app_module, "table", StaleRead())

    status, error = api("PATCH", f"/items/{created['item_id']}", {"width": 300})

    assert status == 409
    record = stored(table, created["item_id"])
    assert record["name"] == "renamed in another tab"
    assert record["width"] == 2400


@pytest.mark.parametrize(
    "body",
    [{"name": "oak plank"}, {"width": 2400}, {"name": "oak plank", "type": "lumber"}],
)
def test_update_with_unchanged_values_does_not_write(table, api, body):
    _, created = api("POST", "/items", OAK)

    status, item = api("PATCH", f"/items/{created['item_id']}", body)

    assert status == 200
    assert item == created
    assert stored(table, created["item_id"])["version"] == 1


def test_update_removing_a_dimension_the_item_lacks_does_not_write(table, api):
    _, created = api("POST", "/items", {"name": "old fridge", "type": "appliance"})

    status, item = api("PATCH", f"/items/{created['item_id']}", {"height": None})

    assert status == 200
    assert item["version"] == 1

# --- DELETE /items/<item_id> ---

def test_delete_returns_204_and_removes_the_item(table, api):
    _, created = api("POST", "/items", OAK)

    status, body = api("DELETE", f"/items/{created['item_id']}")

    assert status == 204
    assert body is None
    assert "Item" not in table.get_item(Key={"PK": "MAKER#m-test", "SK": f"ITEM#{created['item_id']}"})
    assert api("GET", f"/items/{created['item_id']}")[0] == 404


def test_delete_missing_item_returns_404(table, api):
    status, error = api("DELETE", "/items/does-not-exist")

    assert status == 404
    assert error["message"] == "item not found"


def test_delete_twice_returns_404_the_second_time(table, api):
    _, created = api("POST", "/items", OAK)

    api("DELETE", f"/items/{created['item_id']}")
    status, _ = api("DELETE", f"/items/{created['item_id']}")

    assert status == 404
