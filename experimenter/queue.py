import os.path
import socket
import subprocess
import time
import typing
import webbrowser

import redis
import rq
import logging

from experimenter import config, exceptions, utils


_DEFAULT_QUEUE = 'default'
_EMPTIED_MESSAGE = 'queue {} emptied'


def get_connection():
    return redis.StrictRedis(host=config.redis_host)


def get_queue(queue_name: str = _DEFAULT_QUEUE) -> rq.Queue:
    return rq.Queue(queue_name, connection=get_connection())
    
    
def get_worker_message(workers: list, queue_name: str = _DEFAULT_QUEUE):
    num_workers = len(workers)
    message = 'number of workers on queue {}: {}'.format(queue_name, num_workers)
    for it, worker in enumerate(workers):
        success = worker.successful_job_count
        fail = worker.failed_job_count
        if (fail > 0):
            failed_job = get_failed_job(queue_name=queue_name)
            with open ('failed_job.txt', 'w') as failed_file:
                failed_file.write(failed_job)
        message = message+'\n\t\t\t worker: {}'.format(it)
        message = message+'\n\t\t\t\t number of successful jobs: {}'.format(success)
        message = message+'\n\t\t\t\t number of failed jobs: {}'.format(fail) 
    return message
    

def get_failed_job(queue_name='default', job_num=0):
    conn = get_connection()
    #pass name and connection
    reg = rq.registry.FailedJobRegistry(name=queue_name, connection=conn)
    print(len(reg))
    job_ids = reg.get_job_ids()
    if (len(job_ids)<=0):
        return "None"
    job = job_ids[0]
    job = Job.fetch(job, connection=conn)
    return job.exc_info


def get_queue_message(queues: list):
    queues_message = 'getting queues, jobs, and workers'
    for queue in queues:
        queues_message = queues_message + '\n\t number of jobs on queue {}: {}'.format(queue, len(queue))
        workers = rq.Worker.all(queue=queue)
        queues_message = queues_message + '\n\t\t' + str(get_worker_message(workers=workers, queue_name=queue))
        
    return queues_message


def status() -> None:
    conn = get_connection()
    queues = rq.Queue.all(conn)
    queues_message = get_queue_message(queues)
    print('available queues: {}'.format(queues))
    print(queues_message)
    

def empty(queue_name: str = None) -> None:
    if queue_name is None:
        queue_name = _DEFAULT_QUEUE
    queue = get_queue(queue_name)
    queue.empty()
    print(_EMPTIED_MESSAGE.format(queue_name))


def _check_redis_connection() -> typing.Optional[Exception]:
    error = None
    try:
        get_connection().ping()
    except redis.exceptions.RedisError as e:
        error = e
    return error


def make_job(f: typing.Callable, *args: typing.Any, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]:
    return {'f':f, 'args': args, 'kwargs': kwargs}


def enqueue_jobs(
    jobs: typing.Union[typing.Generator, typing.Iterator, typing.Sequence], *,
    job_timeout: int = None, queue_name: str = _DEFAULT_QUEUE,
) -> None:
    """
    Connects to the job queue and enqueues all `jobs`.

    jobs: the jobs to push onto the queue
        Each job must be formatted as a dict with the keys `'f'`, `'args'` (optional), and `'kwargs'` optional.
    """
    if _check_redis_connection() is not None:
        raise exceptions.ServerError(_STATUS_STOPPED_MESSAGE)

    connection = get_connection()
    queue = rq.Queue(queue_name, connection=connection)

    for job in jobs:
        print("Queueing Job - ")
        queue.enqueue(**job, job_timeout=job_timeout)
