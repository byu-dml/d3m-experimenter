import itertools as it
import os
from typing import Any, List, Tuple


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

def execute_pipeline_via_d3m_cli(pipeline_path: str,
    problem_path: str,
    input_path: str,
    output_run_path: str,
    data_random_seed: int,
    data_params: List[Tuple[str,Any]] = None,
    data_pipeline: str = K_FOLD_TABULAR_SPLIT_PIPELINE_ID,
    scoring_pipeline: str = SCORING_PIPELINE_ID,
    input_run_path: str = None,
    metric: str = None,
    scoring_params: List[Tuple[str,Any]] = None,
    scores_path: str = None,
    scoring_random_seed: int = None,
    data_split_file_path: str = None):
    """ TODO: function one-liner

    TODO: function summary

    # data_pipeline_path - 10 fold cross validation default

    Required Arguments:
    ---------------------------------
    pipeline_path -- TODO: arg doc
    problem_path -- TODO: arg doc
    input_path -- TODO: arg doc
    output_run_path -- TODO: arg doc
    data_random_seed -- TODO: arg doc

    Optional Arguments:
    ---------------------------------
    data_params -- TODO: arg doc
    data_pipeline -- TODO: arg doc
    scoring_pipeline -- TODO: arg doc
    input_run_path -- TODO: arg doc
    metric -- TODO: arg doc
    scoring_params -- TODO: arg doc
    scores_path -- TODO: arg doc
    scoring_random_seed -- TODO: arg doc
    data_split_file_path -- TODO: arg doc

    Raises:
    -------
    ValueError: TODO: doc

    Return:
    -------
    TODO: return doc
    """
    args = ['d3m', 'runtime', 'evaluate']

    if (not os.path.isfile(pipeline_path)):
        raise ValueError('\'pipeline_path\' param is not a file')

    if (not os.path.isfile(problem_path)): # TODO: check for URI
        raise ValueError('\'problem_path\' param is not a file')

    if (not os.path.isfile(input_path)): # TODO: check for URI
        raise ValueError('\'input_path\' param is not a file')

    if (not isinstance(output_run_path, str) and output_run_path != '-'):
        # TODO: how to check for nonexistent file? parse?
        raise ValueError('\'output_run_path\' param is not a valid value')

    if (not isinstance(data_random_seed, int)):
        raise TypeError('\'{}\' param is not of type \'{}\''.format('data_random_seed','int'))

    if (input_run_path):
        # TODO: input_run_path validation
        pass

    args.extend(('--pipeline ', pipeline_path))
    args.extend(('--problem', problem_path))
    args.extend(('--input', input_path))
    args.extend(('--output-run', output_run_path))
    args.extend(('--data-random-seed', data_random_seed))

    for data_param in data_params:
        args.extend(('--data-param', data_param[0], data_param[1]))

    if (data_params):
        if (not isinstance(data_params, List)):
            raise TypeError('\'{}\' param is not of type \'{}\''.format('data_params','List'))
        for data_param in data_params:
            args.extend(('--data-param', data_param[0], data_param[1]))

    if (data_pipeline):
        # TODO: how to check if data_pipeline is pipeline id? (guid?)
        args.extend(('--data-pipeline', data_pipeline))

    if (scoring_pipeline):
        # TODO: how to check if scoring_pipeline is pipeline id?
        args.extend(('--scoring-pipeline', scoring_pipeline))

    if (metric):
        # TODO: set of valid metric args?
        args.extend(('--metric', metric))

    if (scoring_params):
        if (not isinstance(scoring_params, List)):
            raise TypeError('\'{}\' param is not of type \'{}\''.format('scoring_params','List'))
        for scoring_param in scoring_params:
            args.extend(('--scoring-param', scoring_param[0], scoring_param[1]))

    if (scores_path):
        # TODO: how to check for nonexistent file? parse?
        args.extend(('--scores', scores_path))

    if (scoring_random_seed):
        if (not isinstance(scoring_random_seed, int)):
            raise TypeError('\'{}\' param is not of type \'{}\''.format('scoring_random_seed','int'))
        args.extend(('--scoring-random-seed', scoring_random_seed))

    if (data_split_file_path):
        if (not os.path.isfile(data_split_file_path)):
            raise ValueError('\'data_split_file_path\' param is not a file')
        args.extend(('--data-split-file', data_split_file_path))

    cli.main(args)

if __name__ == '__main__':
    path = 'README.md'
    execute_pipeline_via_d3m_cli(path,path,path,path,1,[(1,2),(3,4)])
