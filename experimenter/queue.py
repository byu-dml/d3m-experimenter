import os.path
import socket
import subprocess
import time
import typing
import webbrowser

import docker
import redis
import rq

from experimenter import config, exceptions, utils


_DEFAULT_QUEUE = 'default'


_QUEUE_START_SUCCESS_MESSAGE = 'queue successfully started on port {port}'
_QUEUE_STOP_SUCCESS_MESSAGE = 'queue successfully stopped'
_QUEUE_STATUS_RUNNING_MESSAGE = 'queue is running on port {port}'
_QUEUE_STATUS_STOPPED_MESSAGE = 'queue is stopped'
_QUEUE_EMPTIED_MESSAGE = 'queue emptied'


def start() -> None:
    print(config.RedisConfig().host)
    if socket.gethostname() != config.RedisConfig().host:
        raise exceptions.ConfigError(
            'config host \'{}\' does not match actual host \'{}\''.format(
                config.RedisConfig().host, socket.gethostname()
            )
        )

    with utils.DockerClientContext() as docker_client:
        utils.start_docker_container_by_image(
            docker_client,
            config.RedisConfig().docker_image_name,
            ports={config.RedisConfig().docker_port: config.RedisConfig().port},
            volumes={config.RedisConfig().data_dir: {'bind': config.RedisConfig().docker_data_dir, 'mode': 'rw'}},
        )

    utils.wait(
        lambda: _check_redis_connection() is None, timeout=10, interval=1,
        error=exceptions.ServerError('failed to communicate with redis server'),
    )

    print(_QUEUE_START_SUCCESS_MESSAGE.format(port=config.RedisConfig().port))


def stop() -> None:
    if is_running():
        _stop_redis_server()
        print(_QUEUE_STOP_SUCCESS_MESSAGE)
    else:
        print(_QUEUE_STATUS_STOPPED_MESSAGE)


def status() -> None:
    if is_running():
        print(_QUEUE_STATUS_RUNNING_MESSAGE.format(port=config.RedisConfig().port))
    else:
        print(_QUEUE_STATUS_STOPPED_MESSAGE)


def empty() -> None:
    if is_running():
        _empty_rq_queue()
        print(_QUEUE_EMPTIED_MESSAGE)
    else:
        print(_QUEUE_STATUS_STOPPED_MESSAGE)


def start_dashboard(port: int =  None) -> None:
    if port is None:
        port = _DEAFULT_DASHBOARD_HOST_PORT

    if not is_running():
        print(_QUEUE_STATUS_STOPPED_MESSAGE)
    else:
        dashboard_args = ['rq-dashboard', '--port', str(port), '--redis-port', str(_get_redis_port())]
        dashboard_process = subprocess.Popen(dashboard_args)
        time.sleep(1)
        webbrowser.open('http://0.0.0.0:{}'.format(port), new=1)
        dashboard_process.communicate()


def is_running() -> bool:
    redis_container = _get_redis_container()
    return redis_container is not None and redis_container.status == 'running'


def _get_redis_container() -> typing.Optional[docker.models.containers.Container]:
    with utils.DockerClientContext() as docker_client:
        return utils.get_docker_container_by_image(config.RedisConfig().docker_image_name, docker_client)


def _check_redis_connection() -> typing.Optional[Exception]:
    error = None
    try:
        redis.StrictRedis(host=config.RedisConfig().host, port=config.RedisConfig().port, health_check_interval=1).ping()
    except redis.exceptions.RedisError as e:
        error = e
    return error


def _stop_redis_server() -> None:
    with utils.DockerClientContext() as docker_client:
        redis_container = utils.get_docker_container_by_image(config.RedisConfig().docker_image_name, docker_client)
        if redis_container:
            redis_container.stop()
        # TODO: check that the redis container actually stopped


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
    if _check_redis_connection(config.RedisConfig().host, config.RedisConfig().port) is not None:
        raise exceptions.ServerError(_QUEUE_STATUS_STOPPED_MESSAGE)

    connection = redis.StrictRedis(host=config.RedisConfig().host, port=config.RedisConfig().port)
    queue = rq.Queue(_DEFAULT_QUEUE, connection=connection)

    for job in jobs:
        queue.enqueue(**job, job_timeout=job_timeout)


def _empty_rq_queue(queue_name: str = _DEFAULT_QUEUE) -> None:
    connection = redis.StrictRedis(host='localhost', port=config.RedisConfig().port)
    queue = rq.Queue(queue_name, connection=connection)
    queue.empty()


def start_worker(max_jobs: int = None, *, queue_name: str = _DEFAULT_QUEUE) -> None:
    args = [
        'rq', 'worker', queue_name, '--burst', '--url',
        'redis://{}:{}'.format(config.RedisConfig().host, config.RedisConfig().port),
    ]

    if max_jobs is not None:
        args += ['--max-jobs', str(max_jobs)]

    with open(os.devnull) as devnull:
        subprocess.Popen(args, stdout=devnull, stderr=devnull)
