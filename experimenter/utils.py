import contextlib
import functools
import inspect
import io
import json
import os
import time
import typing

from d3m.metadata import problem as problem_module
from d3m.utils import get_datasets_and_problems
from d3m.contrib import pipelines

from experimenter import exceptions, config


DEFAULT_DATASET_DIR = "/datasets"
datasets, problems = None, None


def get_data_prep_pipelines():
    """
    Get data preparation pipelines that are already in the d3m module
    """
    data_prep_dict = dict()
    data_prep_id_list = list()
    #save the relevant paths and ids for data preparation
    data_prep_id_list.append(pipelines.NO_SPLIT_TABULAR_SPLIT_PIPELINE_ID)
    data_prep_dict[pipelines.NO_SPLIT_TABULAR_SPLIT_PIPELINE_ID] = pipelines.NO_SPLIT_TABULAR_SPLIT_PIPELINE_PATH
    data_prep_id_list.append(pipelines.FIXED_SPLIT_TABULAR_SPLIT_PIPELINE_ID)
    data_prep_dict[pipelines.FIXED_SPLIT_TABULAR_SPLIT_PIPELINE_ID] = pipelines.FIXED_SPLIT_TABULAR_SPLIT_PIPELINE_PATH 
    data_prep_id_list.append(pipelines.TRAIN_TEST_TABULAR_SPLIT_PIPELINE_ID)
    data_prep_dict[pipelines.TRAIN_TEST_TABULAR_SPLIT_PIPELINE_ID] = pipelines.TRAIN_TEST_TABULAR_SPLIT_PIPELINE_PATH 
    data_prep_id_list.append(pipelines.K_FOLD_TABULAR_SPLIT_PIPELINE_ID)
    data_prep_dict[pipelines.K_FOLD_TABULAR_SPLIT_PIPELINE_ID] = pipelines.K_FOLD_TABULAR_SPLIT_PIPELINE_PATH
    return data_prep_dict, data_prep_id_list
    

def get_scoring_pipelines():
    """
    Get the scoring pipelines that are already in the d3m module
    """
    scoring_dict = dict()
    scoring_id_list = list()
    #save relevant paths and ids for scoring pipelines
    scoring_id_list.append(pipelines.SCORING_PIPELINE_ID)
    scoring_dict[pipelines.SCORING_PIPELINE_ID] = pipelines.SCORING_PIPELINE_PATH 
    return scoring_dict, scoring_id_list


def get_pipeline_run_output_path(pipeline_path: str, dataset_path: str):
    """
    get the output path of the pipeline run
    """
    output_run_path = []
    #get the digests from the dataset and problem paths
    with open(pipeline_path, 'r') as data:
        pipeline = json.load(data)
        output_run_path.append(pipeline['digest'])
    with open(dataset_path, 'r') as data:
        dataset = json.load(data)
        output_run_path.append(dataset['digest'])
    output_run_path.append(str(random_seed))
    output_run_path = os.path.abspath(os.path.join(config.output_run_path, '_'.join(output_run_path)+'.yaml'))
    return output_run_path
     
 
def get_pipelines_from_d3m(pipeline_id: str = None, types='Data'):
    """Checks if data preparation pipeline is in d3m module,
    if not, return None
    """
    if (types=='Data'):
        dict_ids, id_list = get_data_prep_pipelines()
    elif (types=='Scoring'):
        dict_ids, id_list = get_scoring_pipelines()
    if (pipeline_id in id_list):
        return dict_ids[pipeline_id]
    return None


def save_to_not_exist_file(filename:str = 'dataset_dne.txt', save_id:str = None):
    #create the directory
    os.makedirs(os.path.join('/data','DoesNotExist'),exist_ok=True)
    #get the tag to write or append
    if (os.path.exists(os.path.join('/data','DoesNotExist',filename))):
       tag = 'a' # append to file
    else:
       tag = 'w' # write and create
    #append the non existing value to the file
    with open(os.path.join('/data','DoesNotExist',filename),tag) as to_save:
        to_save.write(save_id+'\n')    


def download_from_database(data, type_to_download: str = 'Pipeline'):
    i_d = data['id']
    save_path = os.path.join('/data', type_to_download, i_d+str('.json')) 
    #create the new directory
    os.makedirs(os.path.dirname(save_path),exist_ok=True)
    #save the file to the directory
    with open(save_path, 'w') as to_save:
        json.dump(data, to_save, indent=4)
    #return the location
    return save_path


def get_dataset_doc_path(dataset_id: str, datasets_dir: str=None) -> str:
    """
    A quick helper function to gather a dataset doc path
    :param dataset_id: the id of the dataset
    :param datasets_dir: the main directory holding all the datasets
    :return the path of the dataset doc
    """
    global datasets, problems
    if datasets is None:
        if datasets_dir is None:
            datasets_dir = os.getenv('DATASETS', DEFAULT_DATASET_DIR)
        datasets, problems = get_datasets_and_problems(datasets_dir)
    try:
        return datasets[dataset_id]
    except:
        #save to dataset id does not exist file
        save_to_not_exist_file('dataset_dne.txt', dataset_id)
        return None


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
    global datasets, problems
    if problems is None:
        if datasets_dir is None:
            datasets_dir = os.getenv('DATASETS', DEFAULT_DATASET_DIR)
        datasets, problems = get_datasets_and_problems(datasets_dir)
    try:
        return problems[problem_id]
    except:
        #save to problem id does not exist file
        save_to_not_exist_file('problem_dne.txt', problem_id)
        return None


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


@contextlib.contextmanager
def redirect_stdout() -> typing.Generator[io.StringIO, None, None]:
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        try:
            yield buf
        finally:
            pass
