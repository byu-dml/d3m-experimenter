from experimenter.pipeline_reconstructor import PipelineReconstructor
import argparse
import json
from experimenter.query import pipeline_generator, test_pipeline
from experimenter.execute_pipeline import execute_pipeline_on_problem
from experimenter.problem import ProblemReference
from d3m.metadata.pipeline import Pipeline
import logging
import logging.config as log_config
from random import seed
from random import randint
from rq import Queue
from tqdm import tqdm
import redis

logger = logging.getLogger(__name__)

def main(**cli_args):
    """The main function for handling python3 seed_swap.py terminal call. This method will
    take a few parameters passed through the terminal and pass parameters to run_seed_swap_on_pipelines().
    In the case of using this script's functionality elsewhere, run_seed_swap_on_pipelines() can be used.
    """
    #run on single pipeline from id
    pipeline_id = None
    if (cli_args['num_pipelines'] == 0):
        pipeline_id = cli_args['test_id']
    #call the function for running the seed swapper on generated pipelines
    run_seed_swap_on_pipelines(
         cli_args['num_seeds'], 
         cli_args['num_pipelines'], 
         cli_args['random_state'], 
         cli_args['queue'],
         pipeline_id,
         cli_args['submitter']
    )
        
def run_seed_swap_on_pipelines(num_seeds:int=10, num_pipelines:int=None, random_state:int=0, queue:str='distribute', pipeline_id:str=None, submitter:str=None):
    """Calls the generator and runs the returned pipelines until the number of seeds that
        a certain pipeline has been run on matches the num_seeds parameter
        Parameters:
            num_seeds - the end goal for the number of seeds a pipeline has been run on
            num_pipelines - the number of pipelines to get from the generator
            random_state - the state from which to generate the new random seeds
            queue - indicates whether or not to queue the pipelines or just run them
    """
    #start the counter
    pipelines_run = 0
    #initialize limit and pipeline id
    limit = num_seeds-1
    pipe_id=pipeline_id
    #check if run on given pipeline
    if (num_pipelines == 0):
        limit=None
        submitter=None
    #loop through the pipeline generator - this is where we would pass num_seeds to the pipeline generator
    for pipeline, problem, used_seeds in pipeline_generator(limit=limit, pipeline_id=pipe_id, submitter=submitter):
        run_on_seeds(pipeline, problem, num_seeds, used_seeds, random_state, queue, pipeline_id)
        #stop the loop if num_pipelines is defined and the corresponding number has been reached
        if num_pipelines is not None:
            pipelines_run += 1
            if pipelines_run >= num_pipelines:
                break
 
def run_on_seeds(pipeline, problem, num_seeds:int=10, used_seeds:list=(), random_state:int=0, queue:str='distribute', pipeline_id:str=None):
    """Runs multiple seeds on the same pipeline and problem
       Parameters:
           pipeline - a pipeline in json-like format
           problem - an instance of ProblemReference in the experimenter
           used_seeds - list of seeds that have already been used on pipeline run
           random_state - the state from which to generate the new random seeds
           queue - indicates whether or not to queue the pipelines or just run on them
    """
    #start the counter
    num_run = len(used_seeds)+1
    #start the random state
    seed(random_state)
    #run pipelines until the correct number has been run
    while (num_run <= num_seeds):
        seed_num = randint(1,10000)
        #if seed is used move on without doing anything
        if (seed_num in used_seeds):
            continue
        #run on seed and update the number of pipeline seeds
        num_run += 1
        run_single_seed(pipeline, problem, seed_num, queue)
    #if in test mode, re-query and display necessary statements of assurance
    if (queue == 'test'):
        run_test(used_seeds, pipeline_id)
        
def run_single_seed(pipeline, problem, seed, queue):
    """Runs a single seed on a pipeline and problem
       Parameters:
           pipeline - a pipeline in json-like format
           problem - an instance of ProblemReference in the experimenter
           queue - indicates whether or not to queue the pipelines or just run them
    """
    pipeline = Pipeline.from_json_structure(pipeline)
    if (queue == 'distribute'):
        #add the pipeline to the queue
        add_to_queue(pipeline, problem, seed, all_metrics=False)
    else:
        #run the pipeline
        execute_pipeline_on_problem(
            pipeline,
            problem=problem,
            volumes_dir='/volumes',
            all_metrics=False,
            random_seed=seed
        )
        
def run_test(used_seeds, pipeline_id):
    """If queue type is test, then make sure that the seed swap worked, by requeueing and
       comparing seeds
       Parameters:
           pipeline_id - the new seeds
           used_seeds - the previous seeds already used on the pipeline_id
    """
    #set logging to debug level
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    #requery
    for pipeline, problem, used_seeds in pipeline_generator(limit=None, pipeline_id=pipeline_id, submitter=None):
        successful = False
        #check if the test was successful
        if (len(new_seeds) >= num_seeds):
            successful = True
        logger.info("Length old seed list: {}, Length new seed list: {}, test successful: {}"
         .format(len(used_random_seeds), len(new_seeds), successful))
        break

def add_to_queue(pipeline, problem, seed, all_metrics):
    queue = connect_to_queue()
    queue.enqueue(
        execute_pipeline_on_problem,
        pipeline,
        problem,
        '/volumes',
        all_metrics,
        seed,
        job_timeout=60 * 12,
    )

def connect_to_queue():
    logger.info("Connecting to Redis")
    try: 
        conn = reds.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
        queue = Queue(connection=conn)
    except Exception:
        raise ConnectionRefusedError
    return queue

def get_cli_args(raw_args=None):
    #get the argument parser
    parser = argparse.ArgumentParser(
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--num_seeds',
                        '-n',
                        help=("The number of seeds indicating how many seeds each pipeline should have"),
                        type=int,
                        default=5
    )
    parser.add_argument('--random_state',
                        '-s',
                        help=("The random state to generate from"),
                        type=int,
                        default=21
    )
    parser.add_argument('--num_pipelines',
                        '-p',
                        help=("The number of pipelines to run before termination"),
                        type=int,
                        default=1
    )
    parser.add_argument('--queue', 
                         '-q',
                         help=("Queue the pipeline or run it on personal machine"),
                         type=str,
                         default='simple'
    )
    parser.add_argument('--test_id',
                        '-i',
                        help=("Id for the unit test"),
                        type=str,
                        default='0457d59b-e0a0-4f00-8b63-1e4685c76997'
    )
    parser.add_argument('--submitter',
                        '-i',
                        help=("the submitter to query for when searching pipeline runs"),
                        type=str,
                        default=None
    )
    args = parser.parse_args(raw_args)
    return args

if __name__ == "__main__":
    args = get_cli_args()
    main(**vars(args))
