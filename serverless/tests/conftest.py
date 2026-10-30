import json
import os
from dataclasses import dataclass
from pathlib import Path

import boto3
import pytest
import yaml
from moto import mock_aws

# Fake credentials, set before anything creates a boto3 client. Environment
# variables beat ~/.aws/config in the credential chain, so even a call that
# escaped the moto mock could never reach the real account.
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "eu-central-1"
os.environ["TABLE_NAME"] = "unit-test-table"
os.environ["DEV_MAKER_ID"] = "m-test"
os.environ["POWERTOOLS_SERVICE_NAME"] = "scrap-overflow-tests"

from api import app as app_module  # noqa: E402  (must come after the environment is set)

SERVERLESS_DIR = Path(__file__).parents[1]


class _CloudFormationLoader(yaml.SafeLoader):
    """Reads template.yaml, ignoring CloudFormation tags such as !Ref."""


_CloudFormationLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


def _table_definition() -> dict:
    """The DBTable properties from template.yaml, so the test table matches the real one."""
    template = yaml.load((SERVERLESS_DIR / "template.yaml").read_text(), Loader=_CloudFormationLoader)
    props = template["Resources"]["DBTable"]["Properties"]
    return {key: props[key] for key in ("AttributeDefinitions", "KeySchema", "GlobalSecondaryIndexes", "BillingMode")}


@dataclass
class FakeLambdaContext:
    """The attributes Powertools' Logger reads from the real Lambda context."""

    function_name: str = "test"
    memory_limit_in_mb: int = 128
    invoked_function_arn: str = "arn:aws:lambda:eu-central-1:123456789012:function:test"
    aws_request_id: str = "test-request-id"


@pytest.fixture()
def table(monkeypatch):
    """A fresh in-memory DynamoDB table (moto), swapped in for the app's real one."""
    with mock_aws():
        fake = boto3.resource("dynamodb").create_table(TableName=os.environ["TABLE_NAME"], **_table_definition())
        monkeypatch.setattr(app_module, "table", fake)
        yield fake


@pytest.fixture()
def api():
    """Call the Lambda handler the way API Gateway would: api("GET", "/items", query={"limit": "5"})."""
    base = json.loads((SERVERLESS_DIR / "events" / "health.json").read_text())

    def call(method, path, body=None, query=None):
        event = dict(
            base,
            httpMethod=method,
            path=path,
            isBase64Encoded=False,
            body=body if body is None or isinstance(body, str) else json.dumps(body),
            queryStringParameters=query,
            multiValueQueryStringParameters={k: [v] for k, v in query.items()} if query else None,
        )
        response = app_module.lambda_handler(event, FakeLambdaContext())
        return response["statusCode"], json.loads(response["body"]) if response.get("body") else None

    return call
