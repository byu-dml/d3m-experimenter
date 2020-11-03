import inspect
import json
import os
import functools
from typing import Callable, Any

from experimenter.problem import ProblemReference
from d3m.metadata import problem as problem_module
from d3m.utils import get_datasets_and_problems


DEFAULT_DATASET_DIR = "/datasets/training_datasets/LL0"
datasets, problems = None, None


def load_datasets_and_problems(datasets_dir: str=None):
    global datasets, problems
    if datasets_dir is None:
        datasets_dir = os.getenv('DATASETS', DEFAULT_DATASET_DIR)
    datasets, problems = get_datasets_and_problems(datasets_dir)


def get_dataset_doc_path(dataset_id: str, datasets_dir: str=None) -> str:
    """
    A quick helper function to gather a dataset doc path
    :param dataset_id: the id of the dataset
    :param datasets_dir: the main directory holding all the datasets
    :return the path of the dataset doc
    """
    global datasets
    if datasets is None:
        load_datasets_and_problems(datasets_dir)
    return datasets[dataset_id]


def get_dataset_doc(dataset_id: str, datasets_dir: str=None) -> dict:
    """
    Gets a dataset doc from a path and loads it
    :param dataset_id: the id of the dataset
    :param datasets_dir: the main directory holding all the datasets
    :return the dataset description object
    """
    dataset_doc_path = get_dataset_doc_path(dataset_id, datasets_dir)
    with open(dataset_doc_path, "r") as f:
        dataset_doc = json.load(f)
    return dataset_doc


def get_problem_path(problem_id: str, datasets_dir: str=None) -> str:
    """
    A quick helper function to gather a problem path
    :param problem_id: the id of the problem
    :param datasets_dir: the main directory holding all the datasets
    :return the path of the problem doc
    """
    global problems
    if problems is None:
        load_datasets_and_problems(datasets_dir)
    return problems[problem_id]


def get_problem_parent_dir(problem_id: str):
    dir_name = problem_id
    if any([x in problem_id for x in {'_problem', '_solution', '_dataset'}]):
        dir_name = '_'.join(problem_id.split('_')[:-1])
    path_chunks = get_problem_path(problem_id).split('/')
    return '/'.join(path_chunks[:path_chunks.index(dir_name)+1])


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


def build_problem_reference(problem_id: str):
   parent_dir = get_problem_parent_dir(problem_id)
   dir_id = parent_dir.split('/')[-1]
   enclosing_dir = '/'.join(parent_dir.split('/')[:-1])
   return ProblemReference(dir_id, '', enclosing_dir)


def dataset_id_exists(dataset_id: str):
    global datasets
    if datasets is None:
        load_datasets_and_problems()
    return dataset_id in datasets


def problem_id_exists(problem_id: str):
    global problems
    if problems is None:
        load_datasets_and_problems()
    return problem_id in problems


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
