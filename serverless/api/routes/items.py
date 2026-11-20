"""Items: the scrap on a maker's shelf."""
import uuid

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, NotFoundError, ServiceError
from botocore.exceptions import ClientError

import db
from db import ITEM_PREFIX, MATCHING_KEYS, matching_attributes, now_iso, record_key, to_api
from parsing import get_maker_id, page_params, parse_item_fields, read_json_body

logger = Logger(child=True)
router = Router()


@router.post("/items")
def create_item():
    maker_id = get_maker_id(router.current_event)
    fields = parse_item_fields(read_json_body(router.current_event))

    item_id = str(uuid.uuid7())
    now = now_iso()
    record = {
        **record_key(maker_id, ITEM_PREFIX, item_id),
        "entity": "item",
        "item_id": item_id,
        "description": "",
        **{k: v for k, v in fields.items() if v is not None},
        "state": "unassigned",
        "version": 1,
        "created_at": now,
        "modified_at": now,
    }
    record |= matching_attributes(maker_id, record)

    db.table.put_item(Item=record, ConditionExpression="attribute_not_exists(PK)")
    logger.info("item created", extra={"item_id": item_id})
    return to_api(record), 201


@router.get("/items/<item_id>")
def get_item(item_id: str):
    maker_id = get_maker_id(router.current_event)

    record = db.table.get_item(Key=record_key(maker_id, ITEM_PREFIX, item_id)).get("Item")
    if record is None:
        raise NotFoundError("item not found")
    return to_api(record)


@router.get("/items")
def list_items():
    items, next_cursor = db.query_page(
        get_maker_id(router.current_event), ITEM_PREFIX, *page_params(router.current_event)
    )
    return {"items": items, "next_cursor": next_cursor}


@router.patch("/items/<item_id>")
def update_item(item_id: str):
    maker_id = get_maker_id(router.current_event)
    changes = parse_item_fields(read_json_body(router.current_event), partial=True)
    if not changes:
        raise BadRequestError("nothing to update")

    record = db.table.get_item(Key=record_key(maker_id, ITEM_PREFIX, item_id)).get("Item")
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
        db.table.put_item(
            Item=merged,
            ConditionExpression="version = :seen",
            ExpressionAttributeValues={":seen": record["version"]},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ServiceError(409, "item changed, reload and try again") from None
        raise
    logger.info("item updated", extra={"item_id": item_id})
    return to_api(merged)


@router.delete("/items/<item_id>")
def delete_item(item_id: str):
    maker_id = get_maker_id(router.current_event)

    response = db.table.delete_item(
        Key=record_key(maker_id, ITEM_PREFIX, item_id), ReturnValues="ALL_OLD"
    )
    if "Attributes" not in response:
        raise NotFoundError("item not found")
    return Response(status_code=204)
