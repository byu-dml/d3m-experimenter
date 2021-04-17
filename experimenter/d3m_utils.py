import json
import os

from typing import List

from d3m import cli as d3m_cli
from d3m.exceptions import StepFailedError

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

    Raises:
    ----------
    """
    d3m_db = D3MMtLDB()
    with open(pipeline_run_path) as pipeline_data:
        pipeline_run = json.load(pipeline_data)
    return D3MMtLDB().save_pipeline_run(pipeline_run)

def create_output_run_filename(pipeline_path: str, problem_path: str,
    input_path: str):
    """ 
    Create output_run path (pipeline run doc)

    Parameters
    ----------
    pipeline_path : path_like str
        path to pipeline document
    problem_path : path_like str
        path to problem document
    input_path : path_like str
        path to input document

    Returns:
    ----------
    file name str

    Raises:
    ----------
    """
    output_run_filename = []

    with open(pipeline_path, 'r') as pipeline:
        output_run_filename.append(json.load(pipeline)['digest'])
    #with open(problem_path, 'r') as problem:
    #    output_run_filename.append(problem['about']['digest'])
    with open(input_path, 'r') as input_f:
        output_run_filename.append(json.load(input_f)['about']['digest'])

    return '_'.join(output_run_filename) + '.json'

def execute_d3m_cli(args: List[str], output_run_path: str) -> None:
    """ 
    Execute the d3m cli
    The 'output_run_path' arg is necessary to check
    if d3m runtime actually wrote the pipeline_run doc

    Parameters
    ----------
    args : list of strs
        list of arguments and values
    output_run_path : path str
        path to pipeline_run doc
        
    Return:
    -------
    None
    
    Raises:
    -------
    """
    try:
        d3m_cli.main(args)
    except StepFailedError as e:
        # we check for this exception to
        # still save to D3M DB when pipeline
        # structure failed
        if (not os.path.isfile(output_run_path)):
            raise e
