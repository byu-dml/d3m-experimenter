mport itertools as it
import json
import os

from typing import Any, List, Tuple
from uuid import UUID

from d3m import cli as d3m_cli
from d3m.d3m.contrib.pipelines import (K_FOLD_TABULAR_SPLIT_PIPELINE_ID, 
    SCORING_PIPELINE_ID)

from experimenter.databases.d3m_mtl import D3MMtLDB

def save_pipeline_run_to_d3m_db(pipeline_run_path: str):
    """ 
    Saves a pipeline run document to the d3m database.

    Parameters
    ----------
    pipeline_run_path : path_like str
        path to pipeline_run document

    Returns:
    ----------
    TODO

    Raises:
    ----------
    TODO
    """
    d3m_db = D3MMtLDB()
    with open(pipeline_run_path) as pipeline_data:
        pipeline_run = json.load(pipeline_data)
    return D3MMtLDB().save_pipeline_run(pipeline_run)

def evaluate_pipeline_on_problem(pipeline_path: str,
    problem_path: str,
    input_path: str,
    data_random_seed: int):
    """ 
    Evaluate pipeline on problem.
    A less verbose form of running d3m's runtime cli 'evaluate' command.
    See 'evaluate_pipeline_via_d3m_cli' for more options for running 
    the 'evaluate' command.

    Parameters
    ----------
    pipeline_path : path_like str
        path to pipeline doc
    problem_path : path_like str 
        path to problem doc
    input_path : path_like str
        path to input full data
    data_random_seed : int   
        random seed to be used for data preparation

    Returns:
    ----------
    None

    Raises:
    ---------------------------------
    OSError
        when a file cannot be opened
    """
    output_run_path = []

    with open(pipeline_path, 'r') as pipeline:
        output_run_path.append(pipeline['properties']['digest'])
    with open(problem_path, 'r') as problem:
        output_run_path.append(problem['properties']['digest'])
    with open(input_path, 'r') as input_f:
        output_run_path.append(input_f['properties']['digest'])

    output_run_path = '_'.join(output_run_path) + '.json'

    evaluate_pipeline_via_d3m_cli(pipeline=pipeline_path, problem=problem_path,
        input=input_path, output_run=output_run_path,
        data_random_seed=data_random_seed)

def evaluate_pipeline_via_d3m_cli(pipeline: str,
    problem: str,
    input: str,
    output_run: str,
    data_random_seed: int):
    """ 
    Evaluate pipeline on problem using d3m's runtime cli. 
    Wrapper function to execute d3m's runtime cli 'evaluate' command.
    Arguments mirror the same arguments using the cli.

    Parameters
    ----------
    pipeline : path_like or uuid4 str
        path to pipeline doc or pipeline ID
    problem : path_like str
        path to problem doc
    input : path_like str
        path to input full data
    output_run : path_like str or '-'
        path where pipeline_run doc
        will be saved.
        use '-' for stdin
    data_random_seed : int
        random seed to use for
        data preparation

    Return:
    -------
    None
    
    Raises:
    -------
    ValueError
        when parameter value is
        invalid
    """
    args = ['d3m', 'runtime', 'evaluate']

    if (not os.path.isfile(pipeline)):
        raise ValueError('\'{}\' param not a file path or pipeline ID'.format('pipeline'))

    if (not os.path.isfile(problem)): 
        raise ValueError('\'{}\' param not a file path'.format('problem'))

    if (not os.path.isfile(input)):
        raise ValueError('\'{}\' param not a file path'.format('input'))

    args.extend(('--pipeline ', pipeline))
    args.extend(('--problem', problem))
    args.extend(('--input', input))
    args.extend(('--output-run', output_run_path))
    args.extend(('--data-random-seed', data_random_seed))

    d3m_cli.main(args)
    save_pipeline_run_to_d3m_db(output_run_path)
