from experimenter.database_communication import PipelineDB
from experimenter.pipeline.run_pipeline import RunPipeline


def execute_pipeline_on_problem(pipe, problem, datasets_dir, volumes_dir):
    # Attempt to run the pipeline
    print("\n On problem {}".format(problem))
    mongo_db = PipelineDB()
    # check if the pipeline has been run:
    if mongo_db.has_duplicate_pipeline_run(problem, pipe.to_json_structure()):
        print("Already ran. Skipping")
        return
    run_pipeline = RunPipeline(datasets_dir, volumes_dir, problem)
    results = run_pipeline.run(problem, pipe)[0]
    score = results[0]
    # fit_pipeline_run = results[1]
    produce_pipeline_run = results[2]
    handle_successful_pipeline_run(produce_pipeline_run.to_json_structure(),
                                            pipe.to_json_structure(), score, problem, mongo_db)


def handle_successful_pipeline_run(pipeline_run, pipeline, score, problem, mongo_db):
    if score["value"][0] == 0:
        # F-SCORE was calculated wrong - quit and don't keep this run
        return
    problem_name = problem.split("/")[-1]
    print_successful_pipeline_run(pipeline_run, pipeline, score)
    write_to_mongo(mongo_db, pipeline_run, pipeline, problem_name)

def print_pipeline_and_problem(pipeline, problem):
    print("Pipeline:")
    print(get_list_vertically(primitive_list_from_pipeline_object(pipeline)))
    print("on problem {} \n\n".format(problem))

def get_primitive_combo_string(pipeline):
    prim_string = ''
    for p in pipeline['steps']:
        prim_string += p['primitive']['id']
    return prim_string


def write_to_mongo(mongo_db, pipeline_run, pipeline, problem_name):
    mongo_db.add_to_pipeline_runs_mongo(pipeline_run)


def print_successful_pipeline_run(pipeline_run, pipeline, score=None):
    primitive_list = primitive_list_from_pipeline_json(pipeline)
    print("Ran pipeline:\n")
    print(get_list_vertically(primitive_list))
    if score is not None:
        print("With a {} of {}".format(score["metric"][0], score["value"][0]))


def primitive_list_from_pipeline_object( pipeline):
    primitives = []
    for p in pipeline.steps:
        primitives.append(p.to_json_structure()['primitive']['python_path'])
    return primitives


def primitive_list_from_pipeline_json( pipeline_json):
    primitives = []
    for step in pipeline_json['steps']:
        primitives.append(step['primitive']['python_path'])
    return primitives


def get_list_vertically( list):
    return '\n'.join(list)