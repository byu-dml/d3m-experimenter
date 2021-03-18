import typing

import redis
import rq

from experimenter import config, exceptions


_DEFAULT_QUEUE = 'default'
_EMPTIED_MESSAGE = 'queue {} emptied'


def get_connection():
    config.validate_redis_host()
    return redis.StrictRedis(host=config.redis_host)


def is_running():
    try:
        get_connection().ping()
        return True
    except (exceptions.ConfigError, redis.exceptions.ConnectionError):
        return False


def get_queue(queue_name: str = _DEFAULT_QUEUE) -> rq.Queue:
    return rq.Queue(queue_name, connection=get_connection())


def status() -> None:
    conn = get_connection()
    print('available queues: {}'.format(rq.Queue.all(conn)))


def enqueue(job, queue_name: str = _DEFAULT_QUEUE, job_timeout: int = None) -> rq.job.Job:
    q = get_queue(queue_name)
    return q.enqueue(**job, job_timeout=job_timeout)


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
        queue.enqueue(**job, job_timeout=job_timeout)
