"""Checks on what the client sends: who is asking, the JSON body and the query string.

Every check raises BadRequestError, which Powertools turns into a 400 response.
"""
import os

from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent

from db import DIMENSIONS

ITEM_TYPES = {"lumber", "metal", "furniture", "appliance"}
ITEMS_EDITABLE = {"name", "type", "description", *DIMENSIONS}
PROJECTS_EDITABLE = {"name", "description"}
REQUIREMENTS_EDITABLE = {"label", "type", *DIMENSIONS}
MAX_REQUIREMENTS = 25  # what one BatchWriteItem request can hold


def get_maker_id(event: BaseProxyEvent) -> str:
    """Who is asking. Every request is the dev maker until sign-in exists."""
    return os.environ["DEV_MAKER_ID"]


def read_json_body(event: BaseProxyEvent) -> dict:
    try:
        body = event.json_body
    except ValueError:
        raise BadRequestError("body must be valid JSON") from None
    if body is None:
        return {}
    if not isinstance(body, dict):
        raise BadRequestError("body must be a JSON object")
    return body


def page_params(event: BaseProxyEvent) -> tuple[int, str | None]:
    """?limit= (1 to 100, default 20) and ?cursor= from the query string."""
    raw = event.get_query_string_value(name="limit", default_value="20")
    try:
        limit = int(raw)
    except ValueError:
        raise BadRequestError("limit must be a whole number") from None
    if not 1 <= limit <= 100:
        raise BadRequestError("limit must be between 1 and 100")
    return limit, event.get_query_string_value(name="cursor")


def reject_unknown(body: dict, allowed: set) -> None:
    unknown = set(body) - allowed
    if unknown:
        raise BadRequestError(f"unknown fields: {', '.join(sorted(unknown))}")


def check_name(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BadRequestError("name is required")
    return value.strip()


def check_text(field: str, value) -> str:
    if not isinstance(value, str):
        raise BadRequestError(f"{field} must be text")
    return value


def check_type(value) -> str:
    if not isinstance(value, str) or value not in ITEM_TYPES:
        raise BadRequestError(f"type must be one of: {', '.join(sorted(ITEM_TYPES))}")
    return value


def check_dimension(dim: str, value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BadRequestError(f"{dim} must be a positive whole number of millimetres")
    return value


def parse_item_fields(body: dict, partial: bool = False) -> dict:
    """Check an item. partial=True (PATCH) makes every field optional."""
    reject_unknown(body, ITEMS_EDITABLE)
    fields = {}
    if not partial or "name" in body:
        fields["name"] = check_name(body.get("name"))
    if not partial or "type" in body:
        fields["type"] = check_type(body.get("type"))
    if "description" in body:
        fields["description"] = check_text("description", body["description"])
    for dim in DIMENSIONS:
        if dim in body:
            # None in a PATCH means "remove this dimension"
            fields[dim] = None if body[dim] is None else check_dimension(dim, body[dim])
    return fields


def parse_project_fields(body: dict, partial: bool = False) -> dict:
    """Check a project. partial=True (PATCH) makes every field optional."""
    reject_unknown(body, PROJECTS_EDITABLE)
    fields = {}
    if not partial or "name" in body:
        fields["name"] = check_name(body.get("name"))
    if "description" in body:
        fields["description"] = check_text("description", body["description"])
    return fields


def parse_requirement_fields(body: dict) -> tuple[dict, int]:
    """Check a new requirement: the fields every copy gets, and how many copies (count)."""
    reject_unknown(body, REQUIREMENTS_EDITABLE | {"count"})
    fields = {"type": check_type(body.get("type"))}
    if "label" in body:
        fields["label"] = check_text("label", body["label"]).strip()
    for dim in DIMENSIONS:
        if dim in body:
            fields[dim] = check_dimension(dim, body[dim])

    count = body.get("count", 1)
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_REQUIREMENTS:
        raise BadRequestError(f"count must be a whole number from 1 to {MAX_REQUIREMENTS}")
    return fields, count
