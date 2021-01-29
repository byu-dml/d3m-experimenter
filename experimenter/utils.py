import contextlib
import functools
import inspect
import io
import json
import os
import time
import typing

import docker

from d3m.metadata import problem as problem_module
from experimenter.problem import ProblemReference
from d3m.utils import get_datasets_and_problems

DEFAULT_DATASET_DIR = "/datasets/training_datasets/LL0"


def get_dataset_doc_path(
    dataset_name: str, dataset_dir: str = DEFAULT_DATASET_DIR
) -> str:
    """
    A quick helper function to gather a problem path
    :param dataset_name: the name of the dataset
    :param dataset_dir: where the main dataset directory is
    :return the path of the problem
    """
    return os.path.join(
        dataset_dir, dataset_name, dataset_name + "_dataset", "datasetDoc.json"
    )


def get_problem_parent_dir(problem_id: str):
    """
    Getting the problem parent directory based on the given problem id and 
    DEFAULT_DATASET_DIR
    """
    dir_name = problem_id
    if any([x in problem_id for x in {'_problem', '_solution', '_dataset'}]):
        dir_name = '_'.join(problem_id.split('_')[:-1])
    path_chunks = get_problem_path(problem_id).split('/')
    return '/'.join(path_chunks[:path_chunks.index(dir_name)+1])

    
def build_problem_reference(problem_id: str):
   parent_dir = get_problem_parent_dir(problem_id)
   dir_id = parent_dir.split('/')[-1]
   enclosing_dir = '/'.join(parent_dir.split('/')[:-1])
   return ProblemReference(dir_id, '', enclosing_dir)
   

def get_dataset_doc(dataset_name: str, dataset_dir: str = DEFAULT_DATASET_DIR) -> dict:
    """
    Gets a dataset doc from a path and loads it
    :param dataset_name: the name of the dataset
    :param dataset_dir: the main directory holding all the datasets
    :return the dataset description object
    """
    dataset_doc_path = get_dataset_doc_path(dataset_name, dataset_dir)
    with open(dataset_doc_path, "r") as f:
        dataset_doc = json.load(f)
    return dataset_doc


def get_problem_path(problem_name: str, dataset_dir: str = DEFAULT_DATASET_DIR) -> str:
    """
    A quick helper function to gather a problem path
    :param problem_name: the name of the problem
    :param dataset_dir: where the main dataset directory is
    :return the path of the problem
    """
    return os.path.join(
        dataset_dir, problem_name, problem_name + "_problem", "problemDoc.json"
    )


def get_problem(problem_path: str, *, parse: bool = True) -> dict:
    """
    Gets problem doc from a path and parses it using d3m
    :param problem_path: the path to get the problem from
    :param parse: whether to parse it or to just load it
    :return the problem description object
    """
    if parse:
        problem_description = problem_module.parse_problem_description(problem_path)
    else:
        with open(problem_path, "r") as f:
            problem_description = json.load(f)
    return problem_description


def get_default_args(f):
    """
    A helper function to get the default arguments for a function
    """
    return {
        k: v.default
        for k, v in inspect.signature(f).parameters.items()
        # if v.default is not inspect.Parameter.empty
    }


def multiply(l: list) -> float:
    """Multiplies all the elements in a list together"""
    return functools.reduce((lambda x, y: x * y), l)


def wait(
    callback: typing.Callable, timeout: int, interval: int = None, error: Exception = None
) -> None:
    """
    Suspends program execution until `callback` returns True or `timeout` seconds have elapsed.
    `callback` is queried every `interval` seconds. Optionally raises `error`, if one is provided.

    callback: a callable to check whether to end the waiting period
        When `callback` returns a truthy value, this method returns.
        `callback` must not require any arguments.

    timeout: the maximum amount of time in seconds to wait
        `timeout` prevents infinite looping in the case that callback never returns a truthy value.

    interval: the amount of time to suspend execution between calls to callback
        `interval` defaults to max(1, int((timeout)**0.5)).

    error: an error to raise if `timeout` seconds have elapsed
    """
    if interval is None:
        interval = max(1, int((timeout)**0.5))

    elapsed_time = 0
    while not callback() and elapsed_time < timeout:
        time.sleep(interval)
        elapsed_time += interval

    if error is not None and not callback():
        raise error


def get_docker_container_by_image(
    image_name: str, docker_client: docker.DockerClient = None
) -> docker.models.containers.Container:
    if docker_client is None:
        docker_client = docker.from_env()

    for container in docker_client.containers.list(all=True):
        if container.attrs['Config']['Image'] == image_name:
            return container

    return None


class DockerClientContext(contextlib.AbstractContextManager):

    def __init__(self) -> None:
        self.client = docker.from_env()

    def __enter__(self) -> docker.DockerClient:
        return self.client

    def __exit__(self, *exc: typing.Any) -> None:
        self.client.close()

@contextlib.contextmanager
def redirect_stdout() -> typing.Generator[io.StringIO, None, None]:
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        try:
            yield buf
        finally:
            pass
