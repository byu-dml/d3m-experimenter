from pipeline_reconstructor import PipelineReconstructor
import argparse
import json
from query import find_pipelines, get_primitive
from experimenter.execute_pipeline import execute_pipeline_on_problem
from experimenter.problem import ProblemReference
from d3m.metadata.pipeline import Pipeline
import numpy as np

def main(**cli_args):
    query_results = find_pipelines(cli_args['primitive_id'],
                                   limit_indexes='first',
                                   limit_results=cli_args['num_to_query'])
    pipeline, swap_loc, datasets_used, used_random_seeds = query_results[0]
    #build the hyperparamters as a list of dictionaries
    hyperparams = build_hyperparams(**cli_args)
    #get the primitive to insert
    primitive_insert = get_primitive(cli_args['primitive_insert'])
    #get the new pipeline with the swapping
    new_pipeline = swap(swap_loc, pipeline, primitive_insert, hyperparams)
    pipeline = json.dumps(pipeline, indent=4)
    run_pipeline(new_pipeline, **cli_args)
    
def build_hyperparams(**cli_args):
    #build hyperparams if passed as argument
    hyper_names = cli_args['hyper_names']
    hyper_data = cli_args['hyper_data']
    if (len(hyper_names) != 0):
        hyperparams = list()
        for it, i in enumerate(hyper_names):
            hyper_dict = dict()
            hyper_dict['name'] = i
            hyper_dict['data'] = hyper_data[it]
            hyperparams.append(hyper_dict)
    else:
        hyperparams = None
        
    return hyperparams
    
def run_pipeline(new_pipeline, **cli_args):
    new_pipeline = Pipeline.from_json(string_or_file=new_pipeline)
    #create ExperimenterDriver instance to be used for running the pipeline
    problem_directory = cli_args['problem_dir']
    dataset_name = cli_args['dataset_name']
    datasets_dir = cli_args['datasets_dir']
    #get problem reference
    problem = ProblemReference(dataset_name, problem_directory, datasets_dir)
    #run the pipeline
    execute_pipeline_on_problem(new_pipeline, problem=problem, volumes_dir='/volumes', all_metrics=True)

def swap(swap_loc, pipeline, primitive_insert, hyperparams):
    pipeline = PipelineReconstructor(pipeline=pipeline)    
    #swap with the different pipeline path
    new_pipeline = pipeline.replace_at_loc(swap_loc, primitive_insert, hyperparams=hyperparams)
    return new_pipeline

def get_cli_args(raw_args=None):
    parser = argparse.ArgumentParser(
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--primitive_id',
                        '-t',
                        help=("What primitive to match in the database query"),
                        default='e193afa1-b45e-4d29-918f-5bb1fa3b88a7'
    )
    parser.add_argument('--num_to_query',
                        '-q',
                        type=int,
                        help=("How many pipelines to return from query"),
                        default=1
    )
    parser.add_argument('--primitive_insert',
                        '-i',
                        help=("The primitive to insert"),
                        default='e193afa1-b45e-4d29-918f-5bb1fa3b88a7'
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
    parser.add_argument('--hyper_data',
                        '-z',
                        type=list,
                        help=("Data to set the hyperparams"),
                        default=[None,1]
    )
    parser.add_argument('--hyper_names',
                        '-n',
                        help=("Name of the hyperparameter"),
                        type=list,
                        default=['categorical_max_absolute_distinct_values', 'categorical_max_ratio_distinct_values']
    )
    args = parser.parse_args(raw_args)
    return args

if __name__ == "__main__":
    args = get_cli_args()
    main(**vars(args))
