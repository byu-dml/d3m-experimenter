import inspect
import json
import os

from d3m.metadata import problem as problem_module


DEFAULT_DATASET_DIR = '/datasets/training_datasets/LL0'


def get_dataset_doc_path(dataset_name, dataset_dir=DEFAULT_DATASET_DIR):
    return os.path.join(
        dataset_dir, dataset_name, dataset_name + '_dataset', 'datasetDoc.json'
    )


def get_dataset_doc(dataset_name, dataset_dir=DEFAULT_DATASET_DIR):
    dataset_doc_path = get_dataset_doc_path(dataset_name, dataset_dir)
    with open(dataset_doc_path, 'r') as f:
        dataset_doc = json.load(f)
    return dataset_doc


def get_problem_path(dataset_name, dataset_dir=DEFAULT_DATASET_DIR):
    return os.path.join(
        dataset_dir, dataset_name, dataset_name + '_problem', 'problemDoc.json'
    )


def get_problem(problem_path, *, parse=True):
    if parse:
        problem_description = problem_module.parse_problem_description(problem_path)
    else:
        with open(problem_path, 'r') as f:
            problem_description = json.load(f)
    return problem_description


def get_default_args(f):
    return {
        k: v.default for k, v in inspect.signature(f).parameters.items()
        # if v.default is not inspect.Parameter.empty
    }
