#!/usr/bin/env python
"""
This file sets the computer it is run on to be a worker in "burst" mode.
This means that it will stop being a worker when the Queue is empty.
The job queue is default of "default" priority.
"""
from rq import Connection, Worker
import redis
try:
    from experimenter.config import redis_host, redis_port
except Exception as E:
    print("Exception: no config file given")
    raise E

conn = redis.StrictRedis(
        host=redis_host,
        port=redis_port)

# Preload libraries
from experimenter_driver import *
# Provide queue names to listen to as arguments to this script,
# similar to rq worker
with Connection():
    qs = sys.argv[1:] or ['default']

    w = Worker(qs, connection=conn)
    print("About to work")
    w.work(burst=True)