"""How records sit in the DynamoDB table: keys, index attributes, hidden fields and paging."""
import base64
import json
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from boto3.dynamodb.conditions import Key

# Routes use `db.table`, never `from db import table`, so tests can swap in a fake table here.
table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

ITEM_PREFIX = "ITEM#"
PROJECT_PREFIX = "PROJECT#"
REQUIREMENT_PREFIX = "REQ#"
DIMENSIONS = ("length", "width", "height")
HIDDEN = {"PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK", "dim_mid", "dim_min", "entity"}
MATCHING_KEYS = ("GSI2PK", "GSI2SK", "dim_mid", "dim_min")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def maker_pk(maker_id: str) -> str:
    """The partition that holds everything a maker owns."""
    return f"MAKER#{maker_id}"


def record_key(maker_id: str, prefix: str, record_id: str) -> dict:
    """The primary key of one record, e.g. record_key("m1", ITEM_PREFIX, "i1")."""
    return {"PK": maker_pk(maker_id), "SK": f"{prefix}{record_id}"}


def set_expression(fields: dict) -> dict:
    """update_item arguments that SET each field, plus modified_at, and add 1 to version."""
    names = {f"#{k}": k for k in fields}
    values = {f":{k}": v for k, v in fields.items()} | {":now": now_iso(), ":one": 1}
    assignments = ", ".join([f"#{k} = :{k}" for k in fields] + ["modified_at = :now"])
    return {
        "UpdateExpression": f"SET {assignments} ADD version :one",
        "ExpressionAttributeNames": names,
        "ExpressionAttributeValues": values,
    }


def matching_attributes(maker_id: str, record: dict) -> dict:
    """GSI2, the matching shelf: unassigned items that have all three dimensions."""
    dims = [record.get(d) for d in DIMENSIONS]
    if record.get("state") != "unassigned" or None in dims:
        return {}
    largest, middle, smallest = sorted(dims, reverse=True)
    return {
        "GSI2PK": f"{maker_pk(maker_id)}#TYPE#{record['type']}",
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
            value = int(value) if value == value.to_integral_value() else float(value)
        out[key] = value
    return out


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
        key = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
    except ValueError:
        raise BadRequestError("cursor is not valid") from None
    if (
        not isinstance(key, dict)
        or set(key) != {"PK", "SK"}
        or key["PK"] != maker_pk(maker_id)
        or not str(key["SK"]).startswith(sk_prefix)
    ):
        raise BadRequestError("cursor is not valid")
    return key


def query_page(
    maker_id: str, prefix: str, limit: int, cursor: str | None, filter_expression=None
) -> tuple[list, str | None]:
    """One page of a maker's records of one kind, newest first."""
    query = {
        "KeyConditionExpression": Key("PK").eq(maker_pk(maker_id)) & Key("SK").begins_with(prefix),
        "ScanIndexForward": False,
        "Limit": limit,
    }
    if filter_expression is not None:
        query["FilterExpression"] = filter_expression
    if cursor:
        query["ExclusiveStartKey"] = decode_cursor(cursor, maker_id, prefix)

    response = table.query(**query)
    return [to_api(r) for r in response["Items"]], encode_cursor(response.get("LastEvaluatedKey"))
