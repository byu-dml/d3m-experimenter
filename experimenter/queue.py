import os.path
import time
import typing

import docker
import redis
import rq

from experimenter import exceptions


DEFAULT_HOST_PORT = 6379
DEFAULT_HOST_DATA_PATH = os.path.join(os.path.expanduser('~'), '.experimenter_cache')

_REDIS_DOCKER_IMAGE_NAME = 'redis:latest'
_REDIS_DOCKER_PORT = 6379
_REDIS_DOCKER_DATA_PATH = '/data'


def start(port: int, data_path: str) -> None:
    start_redis_server(port, data_path)
    print('queue successfully started')


def stop() -> None:
    stop_redis_server()
    print('queue successfully stopped')


def status() -> None:
    docker_client = docker.from_env()
    redis_container = get_docker_container(docker_client, _REDIS_DOCKER_IMAGE_NAME)
    if redis_container is not None and redis_container.status == 'running':
        print('queue is running on port(s): {}'.format(redis_container.ports))
    else:
        print('queue is stopped')


def start_redis_server(port: int, data_path: str) -> None:
    docker_client = docker.from_env()

    redis_container = get_docker_container(docker_client, _REDIS_DOCKER_IMAGE_NAME)
    if redis_container:
        if redis_container.status != 'running':
            redis_container.start()
    else:
        redis_container = docker_client.containers.run(
            _REDIS_DOCKER_IMAGE_NAME, ports={_REDIS_DOCKER_PORT:port},
            volumes={data_path: {'bind': _REDIS_DOCKER_DATA_PATH, 'mode': 'rw'}},
            detach=True, auto_remove=True,
        )

    timeout = 10
    sleep_time = 1
    elapsed_time = 0
    while docker_client.containers.get(redis_container.id).status != 'running' and elapsed_time < timeout:
        time.sleep(sleep_time)
        elapsed_time += sleep_time

    try:
        redis.StrictRedis(host='localhost', port=port, health_check_interval=1).ping()
    except redis.exceptions.RedisError as e:
        raise exceptions.ServerError('Failed to start server, try again') from e


def stop_redis_server() -> None:
    docker_client = docker.from_env()
    redis_container = get_docker_container(docker_client, _REDIS_DOCKER_IMAGE_NAME)
    if redis_container:
        redis_container.stop()


def get_docker_container(docker_client, image_name) -> docker.models.containers.Container:
    for container in docker_client.containers.list(all=True):
        if container.attrs['Config']['Image'] == image_name:
            return container
    return None


def make_job(f, *args, **kwargs):
    return {'f':f, 'args': args, 'kwargs': kwargs}


def enqueue_jobs(jobs: typing.Union[typing.Generator, typing.Iterator, typing.Sequence], queue_host: str, queue_port: int, job_timeout: int = None):
    """
    Connects to the job queue and enqueues all `jobs`.

    jobs: the jobs to push onto the queue
        Each job must be formatted as a dict with the keys `'f'`, `'args'` (optional), and `'kwargs'` optional.
    queue_host: the queue
    """
    connection = redis.StrictRedis(host=queue_host, port=queue_port)
    queue = rq.Queue(connection=connection)

    for job in jobs:
        queue.enqueue(**job, job_timeout=job_timeout)
