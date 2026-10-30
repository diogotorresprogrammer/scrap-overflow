import base64
import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
import boto3

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, NotFoundError, ServiceError
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = Logger()
app = APIGatewayRestResolver()
table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

ITEM_PREFIX = "ITEM#"
ITEM_TYPES = {"lumber", "metal", "furniture", "appliance"}
DIMENSIONS = ("length", "width", "height")
EDITABLE = {"name", "type", "description", *DIMENSIONS}
HIDDEN = {"PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK",
          "GSI2SK", "dim_mid", "dim_min", "entity"}
MATCHING_KEYS = ("GSI2PK", "GSI2SK", "dim_mid", "dim_min")


# --- Helpers ---


def get_maker_id(event) -> str:
    return os.environ["DEV_MAKER_ID"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def item_key(maker_id: str, item_id: str) -> dict:
    return {"PK": f"MAKER#{maker_id}", "SK": f"{ITEM_PREFIX}{item_id}"}


def read_json_body() -> dict:
    try:
        body = app.current_event.json_body
    except ValueError:
        raise BadRequestError("body must be valid JSON") from None
    if body is None:
        return {}
    if not isinstance(body, dict):
        raise BadRequestError("body must be a JSON object")
    return body


def parse_item_fields(body: dict, partial: bool = False) -> dict:
    """Check what the client sent. partial=True (PATCH) makes every field optional."""
    unknown = set(body) - EDITABLE
    if unknown:
        raise BadRequestError(f"unknown fields: {', '.join(sorted(unknown))}")

    fields = {}
    if not partial or "name" in body:
        name = body.get("name")
        if not isinstance(name, str) or not name.strip():
            raise BadRequestError("name is required")
        fields["name"] = name.strip()
    if not partial or "type" in body:
        item_type = body.get("type")
        if not isinstance(item_type, str) or item_type not in ITEM_TYPES:
            raise BadRequestError(
                f"type must be one of: {', '.join(sorted(ITEM_TYPES))}")
        fields["type"] = item_type
    if "description" in body:
        if not isinstance(body["description"], str):
            raise BadRequestError("description must be text")
        fields["description"] = body["description"]
    for dim in DIMENSIONS:
        if dim in body:
            value = body[dim]
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value <= 0):
                raise BadRequestError(
                    f"{dim} must be a positive whole number of millimetres")
            # None in a PATCH means "remove this dimension"
            fields[dim] = value
    return fields


def matching_attributes(maker_id: str, record: dict) -> dict:
    """GSI2, the matching shelf: unassigned items that have all three dimensions."""
    dims = [record.get(d) for d in DIMENSIONS]
    if record.get("state") != "unassigned" or None in dims:
        return {}
    largest, middle, smallest = sorted(dims, reverse=True)
    return {
        "GSI2PK": f"MAKER#{maker_id}#TYPE#{record['type']}",
        "GSI2SK": largest,
        "dim_mid": middle,
        "dim_min": smallest,
    }


def to_api(record: dict) -> dict:
    """Hide storage details and turn DynamoDB's Decimal numbers back into plain numbers."""
    out = {}
    for key, value in record.items():
        if key in HIDDEN:
            continue
        if isinstance(value, Decimal):
            value = int(
                value) if value == value.to_integral_value() else float(value)
        out[key] = value
    return out


def parse_limit(raw: str) -> int:
    """The page size the client asked for: a whole number from 1 to 100."""
    try:
        limit = int(raw)
    except ValueError:
        raise BadRequestError("limit must be a whole number") from None
    if not 1 <= limit <= 100:
        raise BadRequestError("limit must be between 1 and 100")
    return limit


def encode_cursor(key: dict | None) -> str | None:
    """Turn DynamoDB's 'where I stopped' key into a short string for the client."""
    if key is None:
        return None
    return base64.urlsafe_b64encode(json.dumps(key).encode()).decode().rstrip("=")


def decode_cursor(cursor: str, maker_id: str, sk_prefix: str) -> dict:
    """Turn the client's cursor back into a key, refusing anything we didn't hand out.

    sk_prefix is the kind of record being listed ("ITEM#", "PROJECT#"...), so a cursor
    from one list can't be replayed against another.
    """
    try:
        key = json.loads(base64.urlsafe_b64decode(
            cursor + "=" * (-len(cursor) % 4)))
    except ValueError:
        raise BadRequestError("cursor is not valid") from None
    if (
        not isinstance(key, dict)
        or set(key) != {"PK", "SK"}
        or key["PK"] != f"MAKER#{maker_id}"
        or not str(key["SK"]).startswith(sk_prefix)
    ):
        raise BadRequestError("cursor is not valid")
    return key


# --- Routes ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/items")
def create_item():
    maker_id = get_maker_id(app.current_event)
    fields = parse_item_fields(read_json_body())

    item_id = str(uuid.uuid7())
    now = now_iso()
    record = {
        **item_key(maker_id, item_id),
        "entity": "item",
        "item_id": item_id,
        "description": "",
        **{k: v for k, v in fields.items() if v is not None},
        "state": "unassigned",
        "version": 1,
        "created_at": now,
        "modified_at": now
    }
    record |= matching_attributes(maker_id, record)

    table.put_item(Item=record, ConditionExpression="attribute_not_exists(PK)")
    logger.info("item created", extra={"item_id": item_id})

    return to_api(record), 201


@app.get("/items/<item_id>")
def get_item(item_id: str):
    maker_id = get_maker_id(app.current_event)

    record = table.get_item(Key=item_key(maker_id, item_id)).get("Item")
    if record is None:
        raise NotFoundError("item not found")

    return to_api(record)


@app.get("/items")
def list_items():
    maker_id = get_maker_id(app.current_event)
    limit = parse_limit(app.current_event.get_query_string_value(
        name="limit", default_value="20"))
    cursor = app.current_event.get_query_string_value(name="cursor")

    query = {
        "KeyConditionExpression": Key("PK").eq(f"MAKER#{maker_id}") & Key("SK").begins_with(ITEM_PREFIX),
        "ScanIndexForward": False,
        "Limit": limit,
    }
    if cursor:
        query["ExclusiveStartKey"] = decode_cursor(
            cursor, maker_id, ITEM_PREFIX)

    response = table.query(**query)
    return {
        "items": [to_api(record) for record in response["Items"]],
        "next_cursor": encode_cursor(response.get("LastEvaluatedKey")),
    }


@app.patch("/items/<item_id>")
def update_item(item_id: str):
    maker_id = get_maker_id(app.current_event)
    changes = parse_item_fields(read_json_body(), partial=True)
    if not changes:
        raise BadRequestError("nothing to update")

    record = table.get_item(Key=item_key(maker_id, item_id)).get("Item")
    if record is None:
        raise NotFoundError("item not found")
    if all(record.get(k) == v for k, v in changes.items()):
        return to_api(record)

    merged = {
        k: v
        for k, v in (record | changes).items()
        if v is not None and k not in MATCHING_KEYS
    }
    merged |= {"modified_at": now_iso(), "version": record["version"] + 1}
    merged |= matching_attributes(maker_id, merged)

    try:
        table.put_item(
            Item=merged,
            ConditionExpression="version= :seen",
            ExpressionAttributeValues={":seen": record["version"]}
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ServiceError(
                409, "item changed, reload and try again") from None
        raise
    logger.info("item updated", extra={"item_id": item_id})
    return to_api(merged)


@app.delete("/items/<item_id>")
def delete_item(item_id: str):
    maker_id = get_maker_id(app.current_event)

    response = table.delete_item(Key=item_key(
        maker_id, item_id), ReturnValues="ALL_OLD")

    if "Attributes" not in response:
        raise NotFoundError("item not found")

    return Response(status_code=204)


@logger.inject_lambda_context
def lambda_handler(event, context):
    return app.resolve(event, context)
