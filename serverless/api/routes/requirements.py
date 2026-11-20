"""Requirements: the pieces a project needs, each one filled later by an item."""
import uuid

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.exceptions import NotFoundError, ServiceError
from botocore.exceptions import ClientError

import db
from db import PROJECT_PREFIX, REQUIREMENT_PREFIX, now_iso, record_key, to_api
from parsing import get_maker_id, parse_requirement_fields, read_json_body

logger = Logger(child=True)
router = Router()


def save_requirements(maker_id: str, project_id: str, records: list[dict]) -> None:
    record = db.table.get_item(Key=record_key(maker_id, PROJECT_PREFIX, project_id)).get("Item")
    if record is None:
        raise NotFoundError("project not found")

    with db.table.batch_writer() as batch:
        for rec in records:
            batch.put_item(Item=rec)


def delete_requirement_record(maker_id: str, project_id: str, requirement_id: str) -> None:
    try:
        db.table.delete_item(
            Key=record_key(maker_id, REQUIREMENT_PREFIX, requirement_id),
            ConditionExpression="project_id = :project_id AND attribute_not_exists(filled_by)",
            ExpressionAttributeValues={":project_id": project_id},
            ReturnValuesOnConditionCheckFailure="ALL_OLD",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        old = e.response.get("Item")
        if old is None or old["project_id"]["S"] != project_id:
            raise NotFoundError("requirement not found") from None
        raise ServiceError(409, "requirement is filled; unassign its item first") from None


@router.post("/projects/<project_id>/requirements")
def create_requirements(project_id: str):
    maker_id = get_maker_id(router.current_event)
    fields, count = parse_requirement_fields(read_json_body(router.current_event))

    now = now_iso()
    records = []
    for _ in range(count):
        requirement_id = str(uuid.uuid7())
        records.append({
            **record_key(maker_id, REQUIREMENT_PREFIX, requirement_id),
            "GSI1PK": f"{PROJECT_PREFIX}{project_id}",
            "GSI1SK": f"{REQUIREMENT_PREFIX}{requirement_id}",
            "entity": "requirement",
            "requirement_id": requirement_id,
            "project_id": project_id,
            "label": "",
            **fields,
            "version": 1,
            "created_at": now,
            "modified_at": now,
        })

    save_requirements(maker_id, project_id, records)
    logger.info("requirements created", extra={"project_id": project_id, "count": count})
    return {"requirements": [to_api(record) for record in records]}, 201


@router.delete("/projects/<project_id>/requirements/<requirement_id>")
def delete_requirement(project_id: str, requirement_id: str):
    delete_requirement_record(get_maker_id(router.current_event), project_id, requirement_id)
    logger.info("requirement deleted", extra={"project_id": project_id, "requirement_id": requirement_id})
    return Response(status_code=204)
