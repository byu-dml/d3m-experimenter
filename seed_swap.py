from pipeline_reconstructor import PipelineReconstructor
import argparse
import json
from query import find_pipelines
from experimenter.execute_pipeline import execute_pipeline_on_problem
from experimenter.problem import ProblemReference
from d3m.metadata.pipeline import Pipeline
import logging
import logging.config as log_config


logger = logging.getLogger(__name__)

def main(**cli_args):
    #create the function in the query file that returns the seeds that have already been run on and the pipeline to run on
    #seed_runs, pipeline = get_pipeline_seed()
    #now run the pipelines with the new seeds
    for seed in cli_args['seeds']:
        if (seed is in seed_runs):
            logger.info("Seed {} already has a run on the pipeline".format(seed))
        else:
            run_pipeline_seed(pipeline, seed, cli_args)



def run_pipeline_seed(pipeline, seed, **cli_args):
    pipeline = Pipeline.from_json(string_or_file=pipeline)
    #create ExperimenterDriver instance to be used for running the pipeline
    problem_directory = cli_args['problem_dir']
    dataset_name = cli_args['dataset_name']
    datasets_dir = cli_args['datasets_dir']
    #get problem reference
    problem = ProblemReference(dataset_name, problem_directory, datasets_dir)
    #run the pipeline
    execute_pipeline_on_problem(new_pipeline, problem=problem, volumes_dir='/volumes', all_metrics=True, random_seed=seed)


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
    parser.add_argument('--seeds',
                        '-n',
                        help=("The new seeds to test on"),
                        type=list,
                        default=[1,2,3,4,5]
    )
    args = parser.parse_args(raw_args)
    return args

if __name__ == "__main__":
    args = get_cli_args()
    main(**vars(args))
