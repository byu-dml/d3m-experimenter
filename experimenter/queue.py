import os.path
import subprocess
import time
import typing

import docker
import redis
import rq

from experimenter import exceptions, utils


_DEFAULT_HOST_PORT = 6379
_DEFAULT_HOST_DATA_PATH = os.path.join(os.path.expanduser('~'), '.experimenter_cache')
_DEFAULT_QUEUE = 'default'

_REDIS_DOCKER_IMAGE_NAME = 'redis:latest'
_REDIS_DOCKER_PORT = 6379
_REDIS_DOCKER_PORT_PROTOCOL = str(_REDIS_DOCKER_PORT) + '/tcp'
_REDIS_DOCKER_DATA_PATH = '/data'

_QUEUE_START_SUCCESS_MESSAGE = 'queue successfully started on port {port}'
_QUEUE_STOP_SUCCESS_MESSAGE = 'queue successfully stopped'
_QUEUE_STATUS_RUNNING_MESSAGE = 'queue is running on port {port}'
_QUEUE_STATUS_STOPPED_MESSAGE = 'queue is stopped'
_QUEUE_EMPTIED_MESSAGE = 'queue emptied'


def start(port: int = None, data_path: str = None) -> None:
    if port is None:
        port = _DEFAULT_HOST_PORT
    if data_path is None:
        data_path = _DEFAULT_HOST_DATA_PATH

    _start_redis_server(port, data_path)

    print(_QUEUE_START_SUCCESS_MESSAGE.format(port=_get_redis_port()))


def stop() -> None:
    if is_running():
        _stop_redis_server()
    print(_QUEUE_STOP_SUCCESS_MESSAGE)


def status() -> None:
    if is_running():
        print(_QUEUE_STATUS_RUNNING_MESSAGE.format(port=_get_redis_port()))
    else:
        print(_QUEUE_STATUS_STOPPED_MESSAGE)


def empty() -> None:
    if is_running():
        _empty_rq_queue()
        print(_QUEUE_EMPTIED_MESSAGE)
    else:
        print(_QUEUE_STATUS_STOPPED_MESSAGE)


def is_running():
    redis_container = _get_redis_container()
    return redis_container is not None and redis_container.status == 'running'


def _get_redis_container():
    with utils.DockerClientContext() as docker_client:
        return utils.get_docker_container_by_image(_REDIS_DOCKER_IMAGE_NAME, docker_client)


def _get_redis_port() -> int:
    assert is_running()

    error = exceptions.ServerError('unknown queue configuration')

    redis_container = _get_redis_container()
    ports = redis_container.ports

    if _REDIS_DOCKER_PORT_PROTOCOL not in ports:
        raise error
    host_port_bindings = ports[_REDIS_DOCKER_PORT_PROTOCOL]

    if len(host_port_bindings) != 1:
        raise error
    port_binding = host_port_bindings[0]

    if 'HostPort' not in port_binding:
        raise error

    return int(port_binding['HostPort'])


def _start_redis_server(port: int, data_path: str) -> None:
    error = exceptions.ServerError('Failed to start server, try again')

    if not is_running():

        with utils.DockerClientContext() as docker_client:
            redis_container = utils.get_docker_container_by_image(_REDIS_DOCKER_IMAGE_NAME, docker_client)
            if redis_container:
                assert redis_container.status != 'running'
                redis_container.start()
            else:
                redis_container = docker_client.containers.run(
                    _REDIS_DOCKER_IMAGE_NAME, ports={_REDIS_DOCKER_PORT:port},
                    volumes={data_path: {'bind': _REDIS_DOCKER_DATA_PATH, 'mode': 'rw'}},
                    detach=True, auto_remove=True,
                )

        utils.wait(is_running, timeout=10, interval=1, error=error)

    utils.wait(
        lambda: _check_redis_connection(port=port) is None, timeout=10, interval=1, error=error
    )


def _check_redis_connection(host='localhost', port=_DEFAULT_HOST_PORT) -> typing.Optional[Exception]:
    error = None
    try:
        redis.StrictRedis(host=host, port=port, health_check_interval=1).ping()
    except redis.exceptions.RedisError as e:
        error = e
    return error


def _stop_redis_server() -> None:
    with utils.DockerClientContext() as docker_client:
        redis_container = utils.get_docker_container_by_image(_REDIS_DOCKER_IMAGE_NAME, docker_client)
        if redis_container:
            redis_container.stop()
        # TODO: check that the redis container actually stopped


def make_job(f, *args, **kwargs):
    return {'f':f, 'args': args, 'kwargs': kwargs}


def enqueue_jobs(
    jobs: typing.Union[typing.Generator, typing.Iterator, typing.Sequence],
    queue_host: str = None, queue_port: int = None, job_timeout: int = None
) -> None:
    """
    Connects to the job queue and enqueues all `jobs`.

    jobs: the jobs to push onto the queue
        Each job must be formatted as a dict with the keys `'f'`, `'args'` (optional), and `'kwargs'` optional.
    queue_host: the queue
    """
    if queue_host is None:
        queue_host = 'localhost'
    if queue_port is None:
        queue_port = _DEFAULT_HOST_PORT

    if _check_redis_connection(queue_host, queue_port) is not None:
        raise exceptions.ServerError(_QUEUE_STATUS_STOPPED_MESSAGE)

    connection = redis.StrictRedis(host=queue_host, port=queue_port)
    queue = rq.Queue(_DEFAULT_QUEUE, connection=connection)

    for job in jobs:
        queue.enqueue(**job, job_timeout=job_timeout)


def _empty_rq_queue() -> None:
    connection = redis.StrictRedis(host='localhost', port=_get_redis_port())
    queue = rq.Queue(_DEFAULT_QUEUE, connection=connection)
    queue.empty()


def start_worker(queue_host: str = None, queue_port: int = None, max_jobs: int = None):
    if queue_host is None:
        queue_host = 'localhost'
    if queue_port is None:
        queue_port = _DEFAULT_HOST_PORT

    args = [
        'rq', 'worker', _DEFAULT_QUEUE, '--burst', '--url', 'redis://{}:{}'.format(queue_host, queue_port),
    ]
    if max_jobs is not None:
        args += ['--max-jobs', str(max_jobs)]

    with open(os.devnull) as devnull:
        subprocess.Popen(args, stdout=devnull, stderr=devnull)
