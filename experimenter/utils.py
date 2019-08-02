import inspect
import json
import os

from d3m.metadata import problem as problem_module


DEFAULT_DATASET_DIR = '/datasets/training_datasets/LL0'


def get_dataset_doc_path(dataset_name: str, dataset_dir: str = DEFAULT_DATASET_DIR) -> str:
    """
    A quick helper function to gather a problem path
    :param dataset_name: the name of the dataset
    :param dataset_dir: where the main dataset directory is
    :return the path of the problem
    """
    return os.path.join(
        dataset_dir, dataset_name, dataset_name + '_dataset', 'datasetDoc.json'
    )


def get_dataset_doc(dataset_name: str, dataset_dir: str = DEFAULT_DATASET_DIR) -> dict:
    """
    Gets a dataset doc from a path and loads it
    :param dataset_name: the name of the dataset
    :param dataset_dir: the main directory holding all the datasets
    :return the dataset description object
    """
    dataset_doc_path = get_dataset_doc_path(dataset_name, dataset_dir)
    with open(dataset_doc_path, 'r') as f:
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
        dataset_dir, problem_name, problem_name + '_problem', 'problemDoc.json'
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
        with open(problem_path, 'r') as f:
            problem_description = json.load(f)
    return problem_description


def get_default_args(f):
    """
    A helper function to get the default arguments for a function
    """
    return {
        k: v.default for k, v in inspect.signature(f).parameters.items()
        # if v.default is not inspect.Parameter.empty
    }
