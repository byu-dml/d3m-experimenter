import os.path
import socket
import subprocess
import time
import typing
import webbrowser

import docker
import redis
import rq

from experimenter import config, docker_utils, exceptions, utils


_DEFAULT_QUEUE = 'default'


_START_SUCCESS_MESSAGE = 'queue successfully started on port {port}'
_STOP_SUCCESS_MESSAGE = 'queue successfully stopped'
_STATUS_RUNNING_MESSAGE = 'queue is running on port {port}'
_STATUS_STOPPED_MESSAGE = 'queue is stopped'
_QUEUE_LENGTH_MESSAGE = 'number of jobs on queue {name}: {num_jobs}'
_EMPTIED_MESSAGE = 'queue emptied'


def start() -> None:
    if socket.gethostname() != config.RedisConfig().host:
        raise exceptions.ConfigError(
            'config host \'{}\' does not match actual host \'{}\''.format(
                config.RedisConfig().host, socket.gethostname()
            )
        )

    docker_utils.start_container(
        config.RedisConfig().docker_image_name,
        ports={config.RedisConfig().docker_port: config.RedisConfig().port},
        volumes={
            config.RedisConfig().data_dir: {
                'bind': config.RedisConfig().docker_data_dir, 'mode': 'rw'
            }
        },
    )

    utils.wait(
        lambda: _check_redis_connection() is None, timeout=5, interval=1,
        error=exceptions.ServerError('failed to communicate with redis server'),
    )

    print(_START_SUCCESS_MESSAGE.format(port=config.RedisConfig().port))


def is_running():
    return docker_utils.is_container_running(config.RedisConfig().docker_image_name)


def stop() -> None:
    docker_utils.stop_container(config.RedisConfig().docker_image_name)
    print(_STOP_SUCCESS_MESSAGE)

def get_worker_message(workers, queue_name: str = _DEFAULT_QUEUE) -> str:
    num_workers = len(workers)
    message = 'number of workers on queue {}: {}'.format(queue_name, num_workers)
    for it, worker in enumerate(workers):
        success = worker.successful_job_count
        fail = worker.failed_job_count   
        message = message+'\n worker: {}'.format(it)
        message = message+'\n\t number of successful jobs: {}'.format(success)
        message = message+'\n\t number of failed jobs: {}'.format(fail) 
    return message
    
def status(queue_name: str = _DEFAULT_QUEUE) -> None:
    # TODO: report container port instead of config port
    if is_running():
        connection = redis.StrictRedis(host=config.RedisConfig().host, port=config.RedisConfig().port)
        queue = rq.Queue(queue_name, connection=connection)
        workers = rq.Worker.all(queue=queue)
        print(_STATUS_RUNNING_MESSAGE.format(port=config.RedisConfig().port))
        print(_QUEUE_LENGTH_MESSAGE.format(name=queue_name, num_jobs=len(queue)))
        print(get_worker_message(workers,queue_name))
    else:
        print(_STATUS_STOPPED_MESSAGE)


def empty(queue_name: str = _DEFAULT_QUEUE) -> None:
    if is_running():
        connection = redis.StrictRedis(host=config.RedisConfig().host, port=config.RedisConfig().port)
        queue = rq.Queue(queue_name, connection=connection)
        queue.empty()
        print(_EMPTIED_MESSAGE)
    else:
        print(_STATUS_STOPPED_MESSAGE)


def _check_redis_connection() -> typing.Optional[Exception]:
    error = None
    try:
        redis.StrictRedis(host=config.RedisConfig().host, port=config.RedisConfig().port, health_check_interval=1).ping()
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

    connection = redis.StrictRedis(host=config.RedisConfig().host, port=config.RedisConfig().port)
    queue = rq.Queue(_DEFAULT_QUEUE, connection=connection)

    for job in jobs:
        queue.enqueue(**job, job_timeout=job_timeout)


def start_worker(max_jobs: int = None, *, queue_name: str = _DEFAULT_QUEUE) -> None:
    args = [
        'rq', 'worker', queue_name, '--burst', '--url',
        'redis://{}:{}'.format(config.RedisConfig().host, config.RedisConfig().port),
    ]

    if max_jobs is not None:
        args += ['--max-jobs', str(max_jobs)]

    with open(os.devnull) as devnull:
        subprocess.Popen(args, stdout=devnull, stderr=devnull)
