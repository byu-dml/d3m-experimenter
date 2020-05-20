#!/usr/bin/env python
"""
This file sets the computer it is run on to be a worker in "burst" mode.
This means that it will stop being a worker when the Queue is empty.
The job queue is default of "default" priority.
"""
import sys

from rq import Connection, Worker
import redis

from experimenter.config import REDIS_HOST, REDIS_PORT

conn = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

# Preload libraries
from experimenter_driver import *

# Provide queue names to listen to as arguments to this script,
# similar to rq worker
with Connection():
    qs = sys.argv[1:] or ["default"]
    print("Working on queue: {}".format(qs))
    w = Worker(qs, connection=conn)
    print("About to work")
    w.work(burst=True)
