"""
FILE INFORMATION:
This file needs to be a stand alone file so that it can be imported and used by the
experimenter_driver.py.  This is because RQ only accepts a function that is imported
and not defined in __main__.  These functions are what is needed to execute a pipeline
on a problem and can be used by an individual machine, or used in a RQ job queue.
"""
import logging
from typing import List

from d3m.metadata.pipeline import Pipeline

from experimenter.run_fit_pipeline import RunFitPipeline
from experimenter.run_pipeline import RunPipeline
from experimenter.databases.aml_mtl import PipelineDB
from experimenter.databases.d3m_mtl import D3MMtLDB
from experimenter.problem import ProblemReference
from experimenter.config import SAVE_TO_D3M
from experimenter.constants import METRICS_BY_PROBLEM_TYPE
import yaml
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

def execute_pipeline_on_problem(
    pipe: Pipeline,
    problem: ProblemReference,
    volumes_dir: str,
    all_metrics: bool = True,
    random_seed: int = None
):
    """
    The main function to execute a pipeline. Called in `experimenter_driver.py`.
    This function will check if the  pipeline and dataset has been executed before,
    run the pipeline, and record the results.

    :param pipe: the pipeline object that will be executed
    :param problem: a reference to the problem to run the pipeline on.
    :param volumes_dir: a string containing the path to the volumes directory
    :param all_metrics: if `True`, the pipeline will be scored against all metrics
        registered for `problem`'s problem type. If `False`, it will only be scored
        against the metrics listed in `problem`'s description.
    """
    # Validate args
    if all_metrics and problem.problem_type not in METRICS_BY_PROBLEM_TYPE:
        raise ValueError(
            f"cannot compute all metrics for problem {problem.name}, "
            "it does not have a supported problem type."
        )

    # If the experimenter is configured to save documents to the D3M database,
    # we only want to execute and save this pipeline run if it doesn't already
    # exist in the D3M database.
    #if SAVE_TO_D3M and D3MMtLDB().has_pipeline_been_run_on_problem(pipe, problem):
    #    logger.info("Pipeline has already been run on this dataset, SKIPPING.")
    #    return

    metric_names = (
        METRICS_BY_PROBLEM_TYPE[problem.problem_type] if all_metrics else None
    )

    # Attempt to run the pipeline
    logger.info("\n Running pipeline on problem {}".format(problem.name))
    run_pipeline = RunPipeline(volumes_dir, problem, random_seed=random_seed)
    try:
        scores, (fit_result, produce_result) = run_pipeline.run(
            pipeline=pipe, metric_names=metric_names
        )
    except Exception as e:
        logger.exception("pipeline was not successfully run")
        raise e

    score = scores[0]
    # put in the fit pipeline run
    handle_successful_pipeline_run(
        fit_result.pipeline_run.to_json_structure(), pipe, score, problem
    )
    # put in the produce pipeline run
    handle_successful_pipeline_run(
        produce_result.pipeline_run.to_json_structure(), pipe, score
    )


def execute_metafeatures_pipeline_on_problem(
    pipe: Pipeline, problem: ProblemReference, volumes_dir: str
):
    """
    The main function to execute a `metafeatures` pipeline.  Differs from
    `execute_pipeline_on_problem` by only handling metafeatures, and by
    computing them on every subset of the problem e.g. TRAIN, TEST, SCORE, etc.
    Called in `experimenter_driver.py`. This function will run the pipeline,
    and record the results.

    :param pipe: the pipeline object that will be executed
    :param problem: a reference to the problem to run the pipeline on.
    :param volumes_dir: a string containing the path to the volumes directory
    """
    mongo_db = PipelineDB()

    for subset in problem.valid_subsets:
        if problem.has_subset(subset):
            problem.subset = subset
            logger.info(
                f"computing metafeatures for problem {problem.name} ({problem.subset} subset)..."
            )
            # Compute and store the metafeatures for this subset of the problem.
            run_pipeline = RunFitPipeline(volumes_dir, problem)
            try:
                results = run_pipeline.run(pipeline=pipe)
            except Exception as e:
                logger.exception("pipeline was not successfully run")
                print_pipeline(pipe._to_json_structure())
                raise e

            logger.info(results)
            fit_result = results
            mongo_db.add_to_metafeatures(fit_result._to_json_structure())


def handle_successful_pipeline_run(
    pipeline_run: dict, pipeline: Pipeline, score: float, problem=None
):
    """
    Called after a successful pipeline run.  It will output the results to the console
    and write it to the database.

    :param pipeline_run: the pipeline run object that will be recorded
    :param pipeline: the pipeline that was run
    :param score: the results from the execution of the pipeline
    """
    print_pipeline(pipeline.to_json_structure(), score)
    logger.info("Succesfully printed pipeline")
    d3m_db = D3MMtLDB()
    #save the dataset and problem based on problem reference
    if (problem is not None):
        problem_response = d3m_db.save_problem(problem)
        dataset_response = d3m_db.save_dataset(problem)
    if not d3m_db.does_pipeline_exist_in_db(pipeline):
        pipeline_save_response = d3m_db.save_pipeline(pipeline, save_primitives=True)
        if pipeline_save_response.ok:
            logger.info(
                f"pipeline {pipeline.get_digest()} "
                f"saved successfully, response: {pipeline_save_response.json()}"
            )
    #preparation_ref = pipeline_run.get("run", {}).get("data_preparation",{}).get("pipeline")
    #scoring_ref = pipeline_run.get("run", {}).get("scoring", {}).get("pipeline")    
    #add the data prep pipeline
    pipeline_run_save_response = d3m_db.save_pipeline_run(pipeline_run)
    logger.info(pipeline_run_save_response)
    if pipeline_run_save_response.ok:
        logger.info(
            f"pipeline run {pipeline_run['id']} "
            f"saved successfully, response: {pipeline_run_save_response.json()}"
        )


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
    prim_string = ""
    for p in pipeline["steps"]:
        prim_string += p["primitive"]["id"]
    return prim_string


def print_pipeline(pipeline: dict, score: float = None) -> List[str]:
    """
    A helper function for printing a succesful run

    :param pipeline: the pipeline that we will print
    :param score: the results of the metric used in training
    :return primitive_list: a list of all the primitives used in the pipeline
    """
    primitive_list = primitive_list_from_pipeline_json(pipeline)
    logger.info("pipeline:\n")
    logger.info(get_list_vertically(primitive_list))
    if score is not None:
        logger.info("with a {} of {}".format(score["metric"][0], score["value"][0]))
    return primitive_list


def primitive_list_from_pipeline_object(pipeline: Pipeline):
    """
    A helper function to return all the primitives used in a pipeline

    :param pipeline: a pipeline object
    """
    primitives = []
    for p in pipeline.steps:
        primitives.append(p.to_json_structure()["primitive"]["python_path"])
    return primitives


def primitive_list_from_pipeline_json(pipeline_json: dict):
    """
    A helper function to return all the primitives used in a pipeline

    :param pipeline_json a pipeline object in JSON form
    """
    primitives = []
    for step in pipeline_json["steps"]:
        primitives.append(step["primitive"]["python_path"])
    return primitives


def get_list_vertically(list_to_use: list, indent: bool = True):
    """
    A helper function to join a list vertically. Used for debugging printing.
    """
    final_list = ["\t" + item for item in list_to_use] if indent else list_to_use
    return "\n" + "\n".join(final_list)
