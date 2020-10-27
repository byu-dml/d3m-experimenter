from pipeline_reconstructor import PipelineReconstructor
import argparse
import json
from query import pipeline_generator
from experimenter.execute_pipeline import execute_pipeline_on_problem
from experimenter.problem import ProblemReference
from d3m.metadata.pipeline import Pipeline
import logging
import logging.config as log_config
from random import seed
from random import randint


logger = logging.getLogger(__name__)

def main(**cli_args):
    #call the generator
    gen_pipelines = pipeline_generator()
    #get the relevant info from the query                               
    pipeline, problem, used_random_seeds = next(gen_pipelines)
    #now run the pipelines with new generated seeds
    num_run = 0
    #start the random state
    seed(cli_args['random_state'])
    #run pipelines until the correct number has been run
    while (num_run <= cli_args['num_new_seeds']):
        seed_num = randint(1,10000)
        if (seed_num in used_random_seeds):
            num_run = num_run
        else:
            num_run += 1
            run_pipeline_seed(pipeline, seed_num, **cli_args)

def run_pipeline_seed(pipeline, problem, seed, **cli_args):
    pipeline = Pipeline.from_json(string_or_file=pipeline)
    #run the pipeline
    execute_pipeline_on_problem(pipeline, problem=problem, volumes_dir='/volumes', all_metrics=True, random_seed=seed)


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
                        default=1
    )
    args = parser.parse_args(raw_args)
    return args

if __name__ == "__main__":
    args = get_cli_args()
    main(**vars(args))
