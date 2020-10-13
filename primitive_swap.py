from pipeline_reconstructor import PipelineReconstructor
import argparse
import json
from query import find_pipelines
from experimenter.execute_pipeline import execute_pipeline_on_problem
from experimenter.problem import ProblemReference
from d3m.metadata.pipeline import Pipeline

def main(**cli_args):
    query_results = find_pipelines(cli_args['primitive_type'],
                                   limit_indexes='first',
                                   limit_results=cli_args['num_to_query'])
    pipeline, swap_loc = query_results[0]
    #get the primitive to insert
    primitive_insert = dict(cli_args['primitive_insert'])
    #get the new pipeline with the swapping
    new_pipeline = swap(swap_loc, pipeline, primitive_insert)
    pipeline = json.dumps(pipeline, indent=4)
    run_pipeline(new_pipeline, **cli_args)
    
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

def swap(swap_loc, pipeline, primitive_insert):
    pipeline = PipelineReconstructor(pipeline=pipeline)    
    #swap with the different pipeline path
    new_pipeline = pipeline.replace_at_loc(swap_loc, primitive_insert)
    return new_pipeline

def get_cli_args(raw_args=None):
    parser = argparse.ArgumentParser(
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--primitive_type',
                        '-t',
                        help=(
                        "What primitive type to match in the database query"
                        ),
                        choices=["profiler","classifier"],
                        default="profiler"
    )
    parser.add_argument('--num_to_query',
                        '-q',
                        type=int,
                        help=("How many pipelines to return from query"
                        ),
                        default=1
    )
    parser.add_argument('--primitive_insert',
                        '-i',
                        help=("The pipeline path to insert"),
                        default={
				"id": "e193afa1-b45e-4d29-918f-5bb1fa3b88a7",
				"version": "0.2.0",
				"python_path": "d3m.primitives.schema_discovery.profiler.Common",
				"name": "Determine missing semantic types for columns automatically",
				"digest": "b18b86cf0eb6144760f85880f386fa5a9ab55485f8196e68a4a280b03f48ee0c"
			}
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
    args = parser.parse_args(raw_args)
    return args

if __name__ == "__main__":
    args = get_cli_args()
    main(**vars(args))
