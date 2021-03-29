import json
import yaml
import os

from typing import Any, List, Tuple
from experimenter import config, utils, exceptions

from d3m import cli as d3m_cli
from d3m.contrib.pipelines import K_FOLD_TABULAR_SPLIT_PIPELINE_PATH as k_fold_split_path
from experimenter.databases.d3m_mtl import D3MMtLDB


def evaluate(pipeline: str=None,
    problem: str=None,
    input: str=None,
    random_seed: int=0,
    data_pipeline: str=k_fold_split_path,
    data_random_seed: int=0,
    data_params=None,
    scoring_pipeline: str=None,
    scoring_params=None,
    scoring_random_seed: int=0):
    """ 
    Evaluate pipeline on problem using d3m's runtime cli. 
    Wrapper function to execute d3m's runtime cli 'evaluate' command.
    Arguments mirror the same arguments using the cli.
    Only handles cases with a data preparation pipeline in the 
    pipeline run.

    Parameters
    ----------
    pipeline : path_like str
        path to pipeline doc or pipeline ID
    problem : path_like str
        path to problem doc
    input : path_like str
        path to input full data
    random_seed : int
        random seed to used for
        pipeline run
    data_pipeline_path: str
        path to data prepation pipeline
    data_random_seed: int
        random_seed to be used in data preparation
    data_params:
        parameters for data preparation
    scoring_params:
        parameters for scoring pipeline
    scoring_random_seed: int
        random seed for scoring
    scoring_pipeline: str
        path to scoring pipeline 
    Return:
    -------
    None
    
    Raises:
    -------
    ValueError
        when parameter value is
        invalid
    """    
    if (not os.path.isfile(pipeline)):
        raise exceptions.InvalidArgumentValueError('\'{}\' param not a file path'.format('pipeline'))

    if (not os.path.isfile(problem)): 
        raise exceptions.InvalidArgumentValueError('\'{}\' param not a file path'.format('problem'))

    if (not os.path.isfile(input)):
        raise exceptions.InvalidArgumentValueError('\'{}\' param not a file path'.format('input'))
        
    if (not os.path.isfile(data_pipeline)):
        raise exceptions.InvalidArgumentValueError('\'{}\' param not a file path'.format('input'))
        
    if (not os.path.isfile(scoring_pipeline)):
        raise exceptions.InvalidArgumentValueError('\'{}\' param not a file path'.format('input'))
                
    output_run = utils.get_pipeline_run_output_path(pipeline, input, random_seed)
    #get the runtime arguments for the d3m cli    
    args = ['d3m', 'runtime','--random-seed', str(random_seed), 'evaluate',
            '--pipeline', pipeline, '--problem', problem, '--input', input,
            '--output-run', output_run, '--data-pipeline', data_pipeline,
            '--data-random-seed', str(data_random_seed),
            '--scoring-pipeline', scoring_pipeline,
            '--scoring-random-seed', str(scoring_random_seed)]
    #add the data parameters to the cli arguments
    if (data_params is not None):
        for name, value in data_params.items():
            args.extend(('--data-param', name, value))
    #add the scoring parameters to the cli arguments
    if (scoring_params is not None):
        for name, value in scoring_params.items():
            args.extend(('--scoring-param', name, value))
    d3m_cli.main(args)
    #save if proper system variable SAVE_TO_D3M is set to true
    responses = D3MMtLDB().save_pipeline_runs_from_path(output_run)
