import os
import sys
import subprocess
import redis
from rq import Worker
from redis import Redis
import datetime

try:
    redis_host = os.environ['REDIS_HOST']
    redis_port = int(os.environ['REDIS_PORT'])
except Exception as E:
    print("Exception: environment variables not set")
    raise E

conn = redis.StrictRedis(
        host=redis_host,
        port=redis_port)

def kill_workers():
    workers_and_tasks = []
    workers = Worker.all(connection=conn)
    for worker in workers:
        import pdb; pdb.set_trace()
        job = worker.get_current_job()
        if job is not None:
            job.ended_at = datetime.datetime.utcnow()
            worker.failed_queue.quarantine(job, exc_info=("Dead worker", "Moving job to failed queue"))
        worker.register_death()

kill_workers()