from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver

logger = Logger()
app = APIGatewayRestResolver()

@app.get("/health")
def health():
    return {"status": "ok"}

@logger.inject_lambda_context
def lambda_handler(event, context):
    return app.resolve(event, context)
