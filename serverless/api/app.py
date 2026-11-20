"""The Lambda entry point: one API Gateway resolver with every route module plugged in.

Lambda unpacks api/ as the top folder, so modules import each other by plain name (`import db`).
"""
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver

from routes import items, projects, requirements

logger = Logger()
app = APIGatewayRestResolver()
app.include_router(items.router)
app.include_router(projects.router)
app.include_router(requirements.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@logger.inject_lambda_context
def lambda_handler(event, context):
    return app.resolve(event, context)
