from app import create_app
from redis import Redis
from rq import Queue

app = create_app()

redis_conn = Redis(host="redis", port=6379)
q = Queue(connection=redis_conn)