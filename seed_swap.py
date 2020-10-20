from pipeline_reconstructor import PipelineReconstructor
import argparse
import json
from query import find_pipelines
from experimenter.execute_pipeline import execute_pipeline_on_problem
from experimenter.problem import ProblemReference
from d3m.metadata.pipeline import Pipeline
import logging
import logging.config as log_config
from random import seed
from random import randint


logger = logging.getLogger(__name__)

def main(**cli_args):
    #create the function in the query file that returns the seeds that have already been run on and the pipeline to run on
    query_results = find_pipelines('e193afa1-b45e-4d29-918f-5bb1fa3b88a7',
                                   limit_indexes='first',
                                   limit_results=1)
    #get the relevant info from the query                               
    pipeline, swap_loc, datasets_used, used_random_seeds = query_results[0]
    pipeline = json.dumps(pipeline, indent=4)
    #now run the pipelines with new generated seeds
    num_run = 0
    #start the random seed
    seed(cli_args['random_seed'])
    #run pipelines until the correct number has been run
    while (num_run <= cli_args['num_new_seeds']):
        seed_num = randint(1,10000)
        print(seed_num)
        if (seed_num in used_random_seeds):
            num_run = num_run
        else:
            num_run += 1
            run_pipeline_seed(pipeline, seed_num, **cli_args)

def run_pipeline_seed(pipeline, seed, **cli_args):
    pipeline = Pipeline.from_json(string_or_file=pipeline)
    #create ExperimenterDriver instance to be used for running the pipeline
    problem_directory = cli_args['problem_dir']
    dataset_name = cli_args['dataset_name']
    datasets_dir = cli_args['datasets_dir']
    #get problem reference
    problem = ProblemReference(dataset_name, problem_directory, datasets_dir)
    #run the pipeline
    execute_pipeline_on_problem(pipeline, problem=problem, volumes_dir='/volumes', all_metrics=True, random_seed=seed)


def get_cli_args(raw_args=None):
    #get the argument parser
    parser = argparse.ArgumentParser(
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--problem_dir',
                        '-p',
                        help=("The problem to run on the pipeline"),
                        default='seed_datasets_current'
    )
    parser.add_argument('--datasets_dir',
                        '-r',
                        help=("The problem to run on the pipeline"),
                        default='/d3m-experimenter/datasets'
    )
    parser.add_argument('--dataset_name',
                        '-d',
                        help=("The problem to run on the pipeline"),
                        default='185_baseball_MIN_METADATA'
    )
    parser.add_argument('--num_new_seeds',
                        '-n',
                        help=("The number of new seeds to test on"),
                        type=int,
                        default=5
    )
    parser.add_argument('--random_seed',
                        '-s',
                        help=("The random seed to generate from"),
                        type=int,
                        default=21
    )
    args = parser.parse_args(raw_args)
    return args

if __name__ == "__main__":
    args = get_cli_args()
    main(**vars(args))
