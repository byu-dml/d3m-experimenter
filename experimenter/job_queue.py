import time

import docker
import redis


REDIS_DOCKER_IMAGE_NAME = 'redis:latest'
REDIS_DOCKER_PORT = 6379
REDIS_DOCKER_DATA_PATH = '/data'


def start_job_queue(port: int, data_path: str) -> None:
    start_redis_server(port, data_path)


def stop_job_queue() -> None:
    stop_redis_server()


def start_redis_server(port: int, data_path: str) -> None:
    docker_client = docker.from_env()

    redis_container = get_docker_container(docker_client, REDIS_DOCKER_IMAGE_NAME)
    if redis_container:
        if redis_container.status != 'running':
            redis_container.start()
    else:
        redis_container = docker_client.containers.run(
            REDIS_DOCKER_IMAGE_NAME, ports={REDIS_DOCKER_PORT:port},
            volumes={data_path: {'bind': REDIS_DOCKER_DATA_PATH, 'mode': 'rw'}},
            detach=True, auto_remove=True,
        )

    timeout = 10
    sleep_time = 1
    elapsed_time = 0
    while docker_client.containers.get(redis_container.id).status != 'running' and elapsed_time < timeout:
        time.sleep(sleep_time)
        elapsed_time += sleep_time

    redis.StrictRedis(host='localhost', port=port).ping()


def stop_redis_server() -> None:
    docker_client = docker.from_env()
    redis_container = get_docker_container(docker_client, REDIS_DOCKER_IMAGE_NAME)
    if redis_container:
        redis_container.stop()


def get_docker_container(docker_client, image_name) -> docker.models.containers.Container:
    for container in docker_client.containers.list(all=True):
        if container.attrs['Config']['Image'] == image_name:
            return container
    return None
