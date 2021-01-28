import itertools as it
import os

from typing import Any, List, Tuple
from uuid import UUID

from d3m.metadata.pipeline import Pipeline
from d3m import cli

from data_preparation_pipelines import K_FOLD_TABULAR_SPLIT_PIPELINE_ID, SCORING_PIPELINE_ID

def execute_pipeline_on_problem(
    pipe: Pipeline,
    problem: ProblemReference,
    random_seed: int):
    """ TODO: function one-liner

    TODO doc
    """
    pipeline_path = pipeline.id
    problem_path = problem.path
    input_path = problem.dataset_doc_path
    output_run_path = '-'
    data_random_seed = random_seed

    execute_pipeline_via_d3m_cli(pipeline_path, problem_path, input_path,
        output_run_path, data_random_seed)

def execute_pipeline_via_d3m_cli(pipeline: str,
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
    """ TODO: function one-liner

    TODO: function summary

    # data_pipeline_path - 10 fold cross validation default

    Required Arguments:
    ---------------------------------
    pipeline -- TODO: arg doc
    problem -- TODO: arg doc
    input -- TODO: arg doc
    output_run -- TODO: arg doc
    data_random_seed -- TODO: arg doc

    Optional Arguments:
    ---------------------------------
    data_params -- TODO: arg doc
    data_pipeline -- TODO: arg doc
    scoring_pipeline -- TODO: arg doc
    input_run -- TODO: arg doc
    metric -- TODO: arg doc
    scoring_params -- TODO: arg doc
    scores -- TODO: arg doc
    scoring_random_seed -- TODO: arg doc
    data_split_file -- TODO: arg doc

    Raises:
    -------
    TypeError: TODO: doc
    ValueError: TODO: doc

    Return:
    -------
    TODO: return doc
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
        raise ValueError('\'{}\' param not a file path'.format('pipeline'))

    if (not os.path.isfile(problem)): # TODO: check for URI
        raise ValueError('\'{}\' param not a file path'.format('problem'))

    if (not os.path.isfile(input)): # TODO: check for URI
        raise ValueError('\'{}\' param not a file path'.format('input'))

    if (output_run != '-'): # TODO: output_run value check. how to check for nonexistent file? parse?
        raise ValueError('\'{}\' param invalid: {\'-\'}'.format('output_run'))

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
            raise ValueError('\'{}\' param not a file path'.format('data_pipeline'))
        args.extend(('--data-pipeline', data_pipeline))

    if (scoring_pipeline):
        if (not isinstance(scoring_pipeline, str)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('scoring_pipeline','str'))
        if (not os.path.isfile(scoring_pipeline) not is_valid_uuid(scoring_pipeline)):
            raise ValueError('\'{}\' param not a file path'.format('scoring_pipeline'))
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
        # TODO: how to check for nonexistent file? parse?
        args.extend(('--scores', scores_path))

    if (scoring_random_seed):
        if (not isinstance(scoring_random_seed, int)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('scoring_random_seed','int'))
        args.extend(('--scoring-random-seed', scoring_random_seed))

    if (data_split_file):
        if (not isinstance(data_split_file, str)):
            raise TypeError('\'{}\' param not of type \'{}\''.format('data_split_file','str'))
        if (not os.path.isfile(data_split_file)):
            raise ValueError('\'{}\' param invalid value: {file_path, \'-\'}'.format('data_split_file'))
        args.extend(('--data-split-file', data_split_file))

    cli.main(args)

def is_valid_uuid(uuid_to_test: str, version=4):
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

    Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """

    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except Exception:
        return False
    return str(uuid_obj) == uuid_to_test

if __name__ == '__main__':
    path = 'README.md'
    execute_pipeline_via_d3m_cli(path,path,path,path,1,[(1,2),(3,4)])
