#!/usr/bin/env python

import os
from rq import Connection, Worker, get_failed_queue, Queue
import redis
import re

import logging
logger = logging.getLogger(__name__)

def is_phrase_in(phrase, text):
    return re.search(r"\b{}\b".format(phrase), text, re.IGNORECASE) is not None


try:
    redis_host = os.environ['REDIS_HOST']
    redis_port = int(os.environ['REDIS_PORT'])
except Exception as E:
    logger.info("Exception: environment variables not set")
    raise E

conn = redis.StrictRedis(
        host=redis_host,
        port=redis_port)

# Provide queue names to listen to as arguments to this script,
# similar to rq worker
with Connection(connection=conn):
    fq = get_failed_queue()
    job_ids = []
    # registry = queue.failed_job_registry
    requeued_jobs = 0
    logger.info("Going through failed queue")
    for index, job in enumerate(fq.jobs):
        if index == 800000:
            break
        if not index % 1000:
            logger.info("At {} failed jobs".format(index))

        error = job.__dict__["exc_info"]
        try:
            is_nan_issue = is_phrase_in("array must not contain infs or NaNs", error) or \
                           is_phrase_in("Input contains NaN, infinity or a value too large", error)

            is_timeout_issue = is_phrase_in("Task exceeded maximum timeout value", error)
            is_memory_error = is_phrase_in("MemoryError", error)

            is_string_bad_type = is_phrase_in("unsupported operand type", error) or \
                                    is_phrase_in("could not convert string to float", error)

            is_bad_combo = is_phrase_in("Found array with 0 feature", error) or \
                            is_phrase_in("For multi-task outputs, use", error)

            is_bad_matrix = is_phrase_in("numpy.linalg.linalg.LinAlgError", error) or \
                                is_phrase_in("Internal work array size computation failed", error)

            is_bad_rename = is_phrase_in("rename_duplicate_columns.py", error)

            is_workhorse_error = is_phrase_in("Work-horse process was terminated unexpectedly", error)

            if is_nan_issue or is_timeout_issue or is_string_bad_type or is_bad_combo or is_bad_matrix or is_bad_rename:
                continue
            else:
                job_ids.append(job.id)
                requeued_jobs += 1

        except Exception:
            logger.info("Exception")
            job_ids.append(job.id)
            requeued_jobs += 1

    with open('failed_job_ids.txt', 'w') as f:
        for item in job_ids:
            f.write("%s\n" % item)




    logger.info("We requeued {} failed jobs".format(requeued_jobs))

