import json
from dataclasses import dataclass
from pathlib import Path
from api import app

@dataclass
class FakeLambdaContext:
    function_name: str = "test"
    memory_limit_in_mb: int = 128
    invoked_function_arn: str = "arn:aws:lambda:eu-central-1:123456789012:function:test"
    aws_request_id: str = "test-request-id"

def test_lambda_handler():

    event = json.loads(Path("events/health.json").read_text())
    ret = app.lambda_handler(event, FakeLambdaContext())
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert data["status"] == "ok"
