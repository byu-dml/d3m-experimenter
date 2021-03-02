import contextlib
import docker
import typing

from experimenter import exceptions, utils


class DockerClientContext(contextlib.AbstractContextManager):

    def __init__(self) -> None:
        self.client = docker.from_env()

    def __enter__(self) -> docker.DockerClient:
        return self.client

    def __exit__(self, *exc: typing.Any) -> None:
        self.client.close()


def get_container(
    image_name: str, docker_client: docker.DockerClient
) -> docker.models.containers.Container:
    for container in docker_client.containers.list(all=True):
        if container.attrs['Config']['Image'] == image_name:
            return container
    return None


def start_container(
    image_name: str, *, ports: typing.Dict = None, volumes: typing.Dict = None,
    environment: typing.Sequence[str] = None, detach: bool = True, auto_remove: bool = True,
    timeout: int = 5,
) -> None:
    with DockerClientContext() as docker_client:
        container = get_container(image_name, docker_client)

        if container is None:
            container = docker_client.containers.run(
                image_name, ports=ports, volumes=volumes, environment=environment, detach=detach,
                auto_remove=auto_remove,
            )
        elif container.status != 'running':
            container.start()

    # TODO: this often fails on the first attempt, but succeeds on the second

    utils.wait(
        lambda: _is_container_running(container), timeout=timeout, interval=1,
        error=exceptions.ServerError('failed to start container from image {}'.format(image_name))
    )


def is_container_running(image_name: str) -> bool:
    with DockerClientContext() as docker_client:
        container = get_container(image_name, docker_client)
    return _is_container_running(container)


def _is_container_running(container: docker.models.containers.Container) -> bool:
    return container is not None and container.status == 'running'


def stop_container(image_name: str) -> None:
    with DockerClientContext() as docker_client:
        container = get_container(image_name, docker_client)
    if _is_container_running(container):
        container.stop()
