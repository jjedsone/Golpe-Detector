#!/usr/bin/env python3
"""
Worker RQ para processar análises de URLs
Execute com: python worker.py
"""
import os
from dotenv import load_dotenv
from rq import Worker, Queue, Connection
import redis

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if __name__ == '__main__':
    redis_conn = redis.from_url(REDIS_URL)
    with Connection(redis_conn):
        worker = Worker(['default'])
        worker.work()

