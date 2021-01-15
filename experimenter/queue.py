import os.path
import time

import docker
import redis

from experimenter import exceptions


DEFAULT_HOST_PORT = 6379
DEFAULT_HOST_DATA_PATH = os.path.join(os.path.expanduser('~'), '.experimenter_cache')

_REDIS_DOCKER_IMAGE_NAME = 'redis:latest'
_REDIS_DOCKER_PORT = 6379
_REDIS_DOCKER_DATA_PATH = '/data'


def start_queue(port: int, data_path: str) -> None:
    start_redis_server(port, data_path)
    print('queue successfully started')


def stop_queue() -> None:
    stop_redis_server()
    print('queue successfully stopped')


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
