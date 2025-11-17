from fastapi import FastAPI
import redis
import os
from pydantic import BaseModel, HttpUrl
from rq import Queue
import uuid

app = FastAPI()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
r = redis.from_url(REDIS_URL)
q = Queue(connection=r)

class SubmitURL(BaseModel):
    url: HttpUrl
    user_id: int | None = None

@app.get("/")
def index():
    return {"status": "online", "mensagem": "Sistema de proteção educacional ativo."}

@app.post("/submit")
def submit(payload: SubmitURL):
    job_id = str(uuid.uuid4())
    q.enqueue("worker.analyze_url", payload.url, payload.user_id, job_id, job_id=job_id)
    return {"job_id": job_id, "status": "enfileirado"}

