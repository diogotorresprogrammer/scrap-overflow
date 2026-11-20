"""Projects: what a maker builds, its status and whether it's published."""
import uuid

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import BadRequestError, NotFoundError, ServiceError
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

import db
from db import PROJECT_PREFIX, now_iso, record_key, set_expression, to_api
from parsing import get_maker_id, page_params, parse_project_fields, read_json_body, reject_unknown

logger = Logger(child=True)
router = Router()

PROJECT_STATUSES = ("draft", "in_progress", "finished", "archived")
ALLOWED_FROM = {
    "in_progress": ("draft", "finished"),
    "finished": ("in_progress",),
    "archived": ("draft", "in_progress", "finished"),
}
PUBLISHABLE = ("in_progress", "finished")


@router.post("/projects")
def create_project():
    maker_id = get_maker_id(router.current_event)
    fields = parse_project_fields(read_json_body(router.current_event))

    project_id = str(uuid.uuid7())
    now = now_iso()
    record = {
        **record_key(maker_id, PROJECT_PREFIX, project_id),
        "entity": "project",
        "project_id": project_id,
        "GSI1PK": f"{PROJECT_PREFIX}{project_id}",
        "GSI1SK": "PROJECT",
        "description": "",
        **fields,
        "status": "draft",
        "version": 1,
        "created_at": now,
        "modified_at": now,
    }

    db.table.put_item(Item=record, ConditionExpression="attribute_not_exists(PK)")
    logger.info("project created", extra={"project_id": project_id})
    return to_api(record), 201


@router.get("/projects/<project_id>")
def get_project(project_id: str):
    maker_id = get_maker_id(router.current_event)

    record = db.table.get_item(Key=record_key(maker_id, PROJECT_PREFIX, project_id)).get("Item")
    if record is None:
        raise NotFoundError("project not found")
    return to_api(record)


@router.get("/projects")
def list_projects():
    event = router.current_event
    status = event.get_query_string_value(name="status")
    if status is not None and status not in PROJECT_STATUSES:
        raise BadRequestError(f"status must be one of: {', '.join(PROJECT_STATUSES)}")

    projects, next_cursor = db.query_page(
        get_maker_id(event),
        PROJECT_PREFIX,
        *page_params(event),
        filter_expression=Attr("status").eq(status) if status else None,
    )
    return {"projects": projects, "next_cursor": next_cursor}


@router.patch("/projects/<project_id>")
def update_project(project_id: str):
    maker_id = get_maker_id(router.current_event)
    fields = parse_project_fields(read_json_body(router.current_event), partial=True)
    if not fields:
        raise BadRequestError("nothing to update")

    try:
        response = db.table.update_item(
            Key=record_key(maker_id, PROJECT_PREFIX, project_id),
            ConditionExpression="attribute_exists(PK)",
            ReturnValues="ALL_NEW",
            **set_expression(fields),
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NotFoundError("project not found") from None
        raise
    logger.info("project updated", extra={"project_id": project_id})
    return to_api(response["Attributes"])


def update_project_or_explain(maker_id: str, project_id: str, refused: str, **update) -> dict:
    """update_item on a project; a failed condition becomes 404 (missing) or 409 (refused).

    `refused` is the 409 message; "{current}" in it is replaced by the project's status.
    """
    try:
        response = db.table.update_item(
            Key=record_key(maker_id, PROJECT_PREFIX, project_id),
            ReturnValues="ALL_NEW",
            ReturnValuesOnConditionCheckFailure="ALL_OLD",
            **update,
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        if "Item" not in e.response:
            raise NotFoundError("project not found") from None
        # The record inside an error is in DynamoDB's raw format: {"status": {"S": "draft"}}
        current = e.response["Item"]["status"]["S"]
        raise ServiceError(409, refused.format(current=current)) from None
    return to_api(response["Attributes"])


@router.post("/projects/<project_id>/status")
def change_project_status(project_id: str):
    maker_id = get_maker_id(router.current_event)
    body = read_json_body(router.current_event)
    reject_unknown(body, {"status"})
    target = body.get("status")
    if not isinstance(target, str) or target not in ALLOWED_FROM:
        raise BadRequestError(f"status must be one of: {', '.join(ALLOWED_FROM)}")

    fields = {"status": target}
    if target == "finished":
        fields["finished_at"] = now_iso()
    update = set_expression(fields)
    allowed = {f":from{i}": status for i, status in enumerate(ALLOWED_FROM[target])}
    update["ExpressionAttributeValues"] |= allowed
    update["ConditionExpression"] = f"#status IN ({', '.join(allowed)})"
    if target == "archived":
        update["UpdateExpression"] += " REMOVE published_at"

    project = update_project_or_explain(
        maker_id, project_id, f"can't move a {{current}} project to {target}", **update
    )
    logger.info("project status changed", extra={"project_id": project_id, "status": target})
    return project


@router.post("/projects/<project_id>/publish")
def publish_project(project_id: str):
    maker_id = get_maker_id(router.current_event)
    allowed = {f":pub{i}": status for i, status in enumerate(PUBLISHABLE)}

    project = update_project_or_explain(
        maker_id, project_id, "a {current} project can't be published",
        # if_not_exists keeps the first publication date when publishing again
        UpdateExpression="SET published_at = if_not_exists(published_at, :now), modified_at = :now ADD version :one",
        ConditionExpression=f"#status IN ({', '.join(allowed)})",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":now": now_iso(), ":one": 1, **allowed},
    )
    logger.info("project published", extra={"project_id": project_id})
    return project


@router.delete("/projects/<project_id>/publish")
def unpublish_project(project_id: str):
    maker_id = get_maker_id(router.current_event)

    project = update_project_or_explain(
        # attribute_exists(PK) only fails when the project is missing
        maker_id, project_id, "",
        UpdateExpression="SET modified_at = :now ADD version :one REMOVE published_at",
        ConditionExpression="attribute_exists(PK)",
        ExpressionAttributeValues={":now": now_iso(), ":one": 1},
    )
    logger.info("project unpublished", extra={"project_id": project_id})
    return project


@router.delete("/projects/<project_id>")
def delete_project(project_id: str):
    maker_id = get_maker_id(router.current_event)

    response = db.table.delete_item(
        Key=record_key(maker_id, PROJECT_PREFIX, project_id), ReturnValues="ALL_OLD"
    )
    if "Attributes" not in response:
        raise NotFoundError("project not found")
    return Response(status_code=204)
