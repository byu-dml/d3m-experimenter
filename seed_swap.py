from experimenter.pipeline_reconstructor import PipelineReconstructor
import argparse
import json
from experimenter.query import pipeline_generator
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
    #call the generator
    gen_pipelines = pipeline_generator()
    #get the queue argument
    queue = cli_args['queue']
    for i in range(cli_args['num_pipelines']):
        #get the relevant info from the query                               
        pipeline, problem, used_random_seeds = next(gen_pipelines)
        pipeline, problem, used_random_seeds = next(gen_pipelines)
        #now run the pipelines with new generated seeds
        num_run = 1
        #start the random state
        seed(cli_args['random_state'])
        #run pipelines until the correct number has been run
        while (num_run <= cli_args['num_new_seeds']):
            seed_num = randint(1,10000)
            if (seed_num in used_random_seeds):
                num_run = num_run
            else:
                num_run += 1
                run_pipeline_seed(pipeline, problem, seed_num, queue)

def run_pipeline_seed(pipeline, problem, seed, queue):
    pipeline = Pipeline.from_json_structure(pipeline)
    if (queue == 'distribute'):
        #add the pipeline to the queue
        add_to_queue(pipeline, problem, seed, all_metrics=False)
    else:
        #run the pipeline
        execute_pipeline_on_problem(pipeline, problem=problem, volumes_dir='/volumes', all_metrics=False, random_seed=seed)

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
    parser.add_argument('--num_new_seeds',
                        '-n',
                        help=("The number of new seeds to test on"),
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
    args = parser.parse_args(raw_args)
    return args

if __name__ == "__main__":
    args = get_cli_args()
    main(**vars(args))
