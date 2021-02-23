import itertools as it
import json
import os

from typing import Any, List, Tuple
from uuid import UUID

from d3m.metadata.pipeline import Pipeline
from d3m import cli

from experimenter.databases.d3m_mtl import D3MMtLDB
from experimenter.data_preparation_pipelines import K_FOLD_TABULAR_SPLIT_PIPELINE_ID, SCORING_PIPELINE_ID

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
    return D3MMtLDB().save_pipeline_run(pipeline_run_path)

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

    save_pipeline_run_to_d3m_db(output_run_path)

def evaluate_pipeline_via_d3m_cli(pipeline: str,
    problem: str,
    input: str,
    output_run: str,
    data_random_seed: int,
    data_params: List[Tuple[str,Any]] = None,
    data_pipeline: str = K_FOLD_TABULAR_SPLIT_PIPELINE_ID,
    scoring_pipeline: str = SCORING_PIPELINE_ID,
    input_run: str = None,
    metric: str = None,
    scoring_params: List[Tuple[str,Any]] = None,
    scores: str = None,
    scoring_random_seed: int = None,
    data_split_file: str = None):
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
    data_params : list of tuples, optional
        hyper-parameter names and values
        for data preparation.
        None by default
    data_pipeline : path_like str or uuid4 str, optional
        path to data preparation pipeline file
        or pipeline ID.
        K_FOLD_TABULAR_SPLIT_PIPELINE_ID by default
    scoring_pipeline : path_like str or uuid4 str, optional
        path to scoring pipeline file
        or pipeline ID.
        SCORING_PIPELINE_ID by default
    input_run : path_like str or '-', optional
        path to pipeline_run file
        with configuration.
        use '-' for stdin.
        None by default
    metric : str, optional
        metric to use.
        Metric from problem by default
    scoring_params : list of tuples, optional
        hyper-parameter names and values
        for scoring pipeline.
        None by default
    scores : path_like str, optional
        path to save scores.
        None by default
    scoring_random_seed : int, optional
        random seed to use for scoring.
        None by default
    data_split_file : path_like str, optional
        reads the split file and populates
        "primary_index_values" hyper-parameter
        for data preparation pipeline with values
        from the "d3mIndex" column corresponding
        to the test data.
        use '-' for stdin.
        None by default

    Return:
    -------
    None
    
    Raises:
    -------
    TypeError
        when parameter value has 
        incorrect type
    ValueError
        when parameter value is
        invalid
    """
    args = ['d3m', 'runtime', 'evaluate']

    if (not isinstance(pipeline, str)):
        raise TypeError('\'{}\' param not of type \'{}\''.format('pipeline', 'str'))

    if (not isinstance(problem_path, str)):
        raise TypeError('\'{}\' param not of type \'{}\''.format('problem', 'str'))

    if (not isinstance(input, str)):
        raise TypeError('\'{}\' param not of type \'{}\''.format('input', 'str'))

    if (not isinstance(output_run, str)):
        raise TypeError('\'{}\' param not of type \'{}\''.format('output_run', 'str'))

    if (not isinstance(data_random_seed, int)):
        raise TypeError('\'{}\' param not of type \'{}\''.format('data_random_seed','int'))

    if (not os.path.isfile(pipeline) and not is_valid_uuid(pipeline)):
        raise ValueError('\'{}\' param not a file path or pipeline ID'.format('pipeline'))

    if (not os.path.isfile(problem)): # TODO: check for URI
        raise ValueError('\'{}\' param not a file path'.format('problem'))

    if (not os.path.isfile(input)): # TODO: check for URI
        raise ValueError('\'{}\' param not a file path'.format('input'))

    args.extend(('--pipeline ', pipeline))
    args.extend(('--problem', problem))
    args.extend(('--input', input))
    args.extend(('--output-run', output_run_path))
    args.extend(('--data-random-seed', data_random_seed))

    if (input_run):
        if (not isinstance(input_run, str)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('input_run','str'))
        if (not os.path.isfile(input_run) and input_run != '-'):
            raise ValueError('\'{}\' param invalid: {file_path, \'-\'}'.format('input_run'))
        # TODO: input_run validation
        pass

    if (data_params):
        if (not isinstance(data_params, List)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('data_params','List'))
        for data_param in data_params:
            args.extend(('--data-param', data_param[0], data_param[1]))

    if (data_pipeline):
        if (not isinstance(data_pipeline, str)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('data_pipeline','str'))
        if (not os.path.isfile(data_pipeline) and not is_valid_uuid(data_pipeline)):
            raise ValueError('\'{}\' param not a file path or pipeline ID'.format('data_pipeline'))
        args.extend(('--data-pipeline', data_pipeline))

    if (scoring_pipeline):
        if (not isinstance(scoring_pipeline, str)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('scoring_pipeline','str'))
        if (not os.path.isfile(scoring_pipeline) and not is_valid_uuid(scoring_pipeline)):
            raise ValueError('\'{}\' param not a file path or pipeline ID'.format('scoring_pipeline'))
        args.extend(('--scoring-pipeline', scoring_pipeline))

    if (metric):
        if (not isinstance(metric, str)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('metric','str'))
        # TODO: set of valid metric args?
        args.extend(('--metric', metric))

    if (scoring_params):
        if (not isinstance(scoring_params, List)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('scoring_params','List'))
        for scoring_param in scoring_params:
            args.extend(('--scoring-param', scoring_param[0], scoring_param[1]))

    if (scores):
        args.extend(('--scores', scores_path))

    if (scoring_random_seed):
        if (not isinstance(scoring_random_seed, int)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('scoring_random_seed','int'))
        args.extend(('--scoring-random-seed', scoring_random_seed))

    if (data_split_file):
        if (not isinstance(data_split_file, str)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('data_split_file','str'))
        if (data_split_file != '-' and not os.path.isfile(data_split_file)):
            raise ValueError('\'{}\' param invalid value: {file_path, \'-\'}'.format('data_split_file'))
        args.extend(('--data-split-file', data_split_file))

    cli.main(args)

def is_valid_uuid(uuid_to_test: str, version=4):
    """
    Check if uuid_to_test is a valid UUID.

    Parmaters
    -------
    uuid_to_test : str
        str to test if valid uuid
    version : {1, 2, 3, 4}
        version of uuid for which to test
    
    Returns
    -------
    bool
        `True` if uuid_to_test is a valid UUID,
        otherwise `False`
    
    Raises:
    -------
    TypeError
        when str is not valid uuid
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except TypeError:
        return False
    return str(uuid_obj) == uuid_to_test
