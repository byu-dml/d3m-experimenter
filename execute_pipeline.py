"""
FILE INFORMATION:
This file needs to be a stand alone file so that it can be imported and used by the experimenter_driver.py.  This is
because RQ only accepts a function that is imported and not defined in __main__.  These functions are what is needed
to execute a pipeline on a problem and can be used by an individual machine, or used in a RQ job queue.
"""
from d3m import Pipeline
from typing List
from experimenter.database_communication import PipelineDB
from experimenter.run_fit_pipeline import RunFitPipeline
from experimenter.run_pipeline import RunPipeline

import logging
logger = logging.getLogger(__name__)


def execute_pipeline_on_problem(pipe: Pipeline, problem: str, datasets_dir: str, volumes_dir: str):
    """
    The main function to execute a pipeline.  Called in `experimenter_driver.py`  This function will check if the 
    pipeline and dataset has been executed before, run the pipeline, and record the results

    :param pipe: the pipeline object that will be executed
    :param problem: the path to the problemDoc of the particular dataset
    :param datasets_dir: a string containing the main directory of datasets
    :param volumes_dir: a string containing the path to the volumes directory
    """
    # Attempt to run the pipeline
    logger.info("\n On problem {}".format(problem))
    mongo_db = PipelineDB()
    collection_name = get_pipeline_run_collection_from_primitives(primitive_list_from_pipeline_object(pipe))

    # check if the pipeline has been run:
    if mongo_db.should_not_run_pipeline(problem, pipe.to_json_structure(), collection_name):
        logger.info("Documents are missing or pipeline has already been run. SKIPPING")
        return
    run_pipeline = RunPipeline(datasets_dir, volumes_dir, problem)
    try:
        results = run_pipeline.run(pipeline=pipe)[0]
    except Exception as e:
        logger.info("ERROR: pipeline was not successfully run due to {}".format(e))
        print_pipeline_run(pipe.to_json_structure())
        raise e

    score = results[0]
    fit_pipeline_run = results[1]
    produce_pipeline_run = results[2]
    # put in the fit pipeline
    handle_successful_pipeline_run(fit_pipeline_run.to_json_structure(),
                                            pipe.to_json_structure(), score, problem, mongo_db, collection_name)
    # put in the produce pipeline
    handle_successful_pipeline_run(produce_pipeline_run.to_json_structure(),
                                   pipe.to_json_structure(), score, problem, mongo_db, collection_name)


def execute_fit_pipeline_on_problem(pipe: Pipeline, problem: str, datasets_dir: str, volumes_dir: str):
    """
    The main function to execute a `metafeatures` pipeline.  Differs from `execute_pipeline_on_problem` by only handling metafeatures
    TODO: combine this with `execute_pipeline_on_problem`
    Called in `experimenter_driver.py`  This function will check if the 
    pipeline and dataset has been executed before, run the pipeline, and record the results

    :param pipe: the pipeline object that will be executed
    :param problem: the path to the problemDoc of the particular dataset
    :param datasets_dir: a string containing the main directory of datasets
    :param volumes_dir: a string containing the path to the volumes directory
    """
    # Attempt to run the pipeline
    logger.info("\n On problem {}".format(problem))
    mongo_db = PipelineDB()
    collection_name = get_pipeline_run_collection_from_primitives(primitive_list_from_pipeline_object(pipe))
    # check if the pipeline has been run:
    if mongo_db.should_not_run_pipeline(problem, pipe.to_json_structure(), collection_name, skip_pipeline=True)\
            or mongo_db.metafeature_run_already_exists(problem, pipe.to_json_structure()):
        logger.info("Documents are missing or pipeline has already been run. SKIPPING")
        return
    run_pipeline = RunFitPipeline(datasets_dir, volumes_dir, problem)
    try:
        results = run_pipeline.run(pipeline=pipe)
    except Exception as e:
        logger.info("ERROR: pipeline was not successfully run due to {}".format(e))
        print_pipeline_run(pipe._to_json_structure())
        raise e

    logger.info(results)
    fit_pipeline_run = results
    mongo_db.add_to_metafeatures(fit_pipeline_run._to_json_structure())


def get_pipeline_run_collection_from_primitives(primitive_list: list):
    """
    A helper function to determine if a primitive used for checking baselines was used in the pipeline
    :param primitive_list: a list of string primitive names used in the pipeline
    """
    baseline_primitives = [ 'd3m.primitives.classification.search.AutoSKLearn']
    for primitive in baseline_primitives:
        if primitive in primitive_list:
            return "automl_pipeline_runs"
    else:
        return "pipeline_runs"


def handle_successful_pipeline_run(pipeline_run: dict, pipeline: dict, score: float, problem: str, mongo_db: PipelineDB, collection_name: str):
    """
    Called after a successful pipeline run.  It will output the results to the console and write it to the database

    :param pipeline_run: the pipeline run object that will be recorded
    :param pipeline: the pipeline that was run
    :param score: the results from the execution of the pipeline
    :param problem: the problem that was used
    :param mongo_db: a connection to the MongoDB database
    """
    if score["value"][0] == 0:
        # F-SCORE was calculated wrong - quit and don't keep this run
        return
    primitive_list = print_pipeline_run(pipeline, score)
    write_to_mongo_pipeline_run(mongo_db, pipeline_run, collection_name)


def print_pipeline_and_problem(pipeline: dict, problem: str):
    """
    A simple function to print the pipeline and problem, for debugging

    :param pipeline: the pipeline that was executed
    :param problem: the dataset/problem that was used
    """
    logger.info("Pipeline:")
    logger.info(get_list_vertically(primitive_list_from_pipeline_object(pipeline)))
    logger.info("on problem {} \n\n".format(problem))

def get_primitive_combo_string(pipeline):
    prim_string = ''
    for p in pipeline['steps']:
        prim_string += p['primitive']['id']
    return prim_string


def write_to_mongo_pipeline_run(mongo_db: PipelineDB, pipeline_run: dict, collection_name: str):
    """
    A function to write a pipeline_run document to a database.  A wrapper for the function in database_communication.py

    :param mongo_db: the database connection
    :param pipeline_run: the json object to be written to the database
    :param collection_name: the name of the pipeline_run collection to insert it into: baselines or pipeline_runs
    """
    mongo_db.add_to_pipeline_runs_mongo(pipeline_run, collection_name)


def print_pipeline_run(pipeline: dict, score: float = None) -> List[str]:
    """
    A helper function for printing a succesful run

    :param pipeline: the pipeline that we will print
    :param score: the results of the metric used in training
    :return primitive_list: a list of all the primitives used in the pipeline
    """
    primitive_list = primitive_list_from_pipeline_json(pipeline)
    logger.info("Ran pipeline:\n")
    logger.info(get_list_vertically(primitive_list))
    if score is not None:
        logger.info("With a {} of {}".format(score["metric"][0], score["value"][0]))
    return primitive_list


def primitive_list_from_pipeline_object(pipeline: Pipeline):
    """
    A helper function to return all the primitives used in a pipeline

    :param pipeline: a pipeline object
    """
    primitives = []
    for p in pipeline.steps:
        primitives.append(p.to_json_structure()['primitive']['python_path'])
    return primitives


def primitive_list_from_pipeline_json(pipeline_json: dict):
    """
    A helper function to return all the primitives used in a pipeline

    :param pipeline_json a pipeline object in JSON form
    """
    primitives = []
    for step in pipeline_json['steps']:
        primitives.append(step['primitive']['python_path'])
    return primitives


def get_list_vertically(list_to_use: list):
    """
    A helper function to join a list vertically.  Used for debugging printing.
    """
    return '\n'.join(list_to_use)
