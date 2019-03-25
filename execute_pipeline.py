"""
FILE INFORMATION:
This file needs to be a stand alone file so that it can be imported and used by the experimenter_driver.py.  This is
because RQ only accepts a function that is imported and not defined in __main__.  These functions are what is needed
to execute a pipeline on a problem and can be used by an individual machine, or used in a RQ job queue.
"""

from experimenter.database_communication import PipelineDB
from experimenter.run_pipeline import RunPipeline


"""
The main function to execute a pipeline.  Called in `experimenter_driver.py`  This function will check if the 
pipeline and dataset has been executed before, run the pipeline, and record the results

:param pipe: the pipeline object that will be executed
:param problem: the path to the problemDoc of the particular dataset
:param datasets_dir: a string containing the main directory of datasets
:param volumes_dir: a string containing the path to the volumes directory
"""
def execute_pipeline_on_problem(pipe, problem, datasets_dir, volumes_dir):
    # Attempt to run the pipeline
    print("\n On problem {}".format(problem))
    mongo_db = PipelineDB()
    collection_name = get_pipeline_run_collection_from_primitives(primitive_list_from_pipeline_object(pipe))

    # check if the pipeline has been run:
    if mongo_db.has_duplicate_pipeline_run(problem, pipe.to_json_structure(), collection_name):
        print("Already ran. Skipping")
        return
    run_pipeline = RunPipeline(datasets_dir, volumes_dir, problem)
    try:
        results = run_pipeline.run(pipeline=pipe)[0]
    except Exception as e:
        print("ERROR: pipeline was not successfully run due to {}".format(e))
        print_successful_pipeline_run(pipe.to_json_structure())
        raise e

    score = results[0]
    # fit_pipeline_run = results[1]
    produce_pipeline_run = results[2]
    handle_successful_pipeline_run(produce_pipeline_run.to_json_structure(),
                                            pipe.to_json_structure(), score, problem, mongo_db, collection_name)


"""
Called after a successful pipeline run.  It will output the results to the console and write it to the database

:param pipeline_run: the pipeline run object that will be recorded
:param pipeline: the pipeline that was run
:param score: the results from the execution of the pipeline
:param problem: the problem that was used
:param mongo_db: a connection to the MongoDB database
"""

"""
A helper function to determine if a primitive used for checking baselines was used in the pipeline
:param primitive_list: a list of string primitive names used in the pipeline
:return collection_name: the name of the collection to insert this pipeline into
"""
def get_pipeline_run_collection_from_primitives(primitive_list):
    baseline_primitives = [ 'd3m.primitives.classification.search.AutoSKLearn']
    for primitive in baseline_primitives:
        if primitive in primitive_list:
            return "automl_pipeline_runs"
    else:
        return "pipeline_runs"


def handle_successful_pipeline_run(pipeline_run, pipeline, score, problem, mongo_db, collection_name):
    if score["value"][0] == 0:
        # F-SCORE was calculated wrong - quit and don't keep this run
        return
    primitive_list = print_successful_pipeline_run(pipeline, score)
    # write_to_mongo_pipeline_run(mongo_db, pipeline_run, collection_name)


"""
A simple function to print the pipeline and problem, for debugging

:param pipeline: the pipeline that was executed
:param problem: the dataset/problem that was used
"""
def print_pipeline_and_problem(pipeline, problem):
    print("Pipeline:")
    print(get_list_vertically(primitive_list_from_pipeline_object(pipeline)))
    print("on problem {} \n\n".format(problem))

def get_primitive_combo_string(pipeline):
    prim_string = ''
    for p in pipeline['steps']:
        prim_string += p['primitive']['id']
    return prim_string

"""
A function to write a pipeline_run document to a database.  A wrapper for the function in database_communication.py

:param mongo_db: the database connection
:param pipeline_run: the json object to be written to the database
:param collection_name: the name of the pipeline_run collection to insert it into: baselines or pipeline_runs
"""
def write_to_mongo_pipeline_run(mongo_db, pipeline_run, collection_name):
    mongo_db.add_to_pipeline_runs_mongo(pipeline_run, collection_name)


"""
A helper function for printing a succesful run

:param pipeline: the pipeline that we will print
:param score: the results of the metric used in training
:return primitive_list: a list of all the primitives used in the pipeline
"""
def print_successful_pipeline_run(pipeline, score=None):
    primitive_list = primitive_list_from_pipeline_json(pipeline)
    print("Ran pipeline:\n")
    print(get_list_vertically(primitive_list))
    if score is not None:
        print("With a {} of {}".format(score["metric"][0], score["value"][0]))
    return primitive_list


"""
A helper function to return all the primitives used in a pipeline

:param pipeline: a pipeline object
"""
def primitive_list_from_pipeline_object(pipeline):
    primitives = []
    for p in pipeline.steps:
        primitives.append(p.to_json_structure()['primitive']['python_path'])
    return primitives


"""
A helper function to return all the primitives used in a pipeline

:param pipeline_json a pipeline object in JSON form
"""
def primitive_list_from_pipeline_json( pipeline_json):
    primitives = []
    for step in pipeline_json['steps']:
        primitives.append(step['primitive']['python_path'])
    return primitives


"""
A helper function to join a list vertically.  Used for debugging printing.
"""
def get_list_vertically( list):
    return '\n'.join(list)
