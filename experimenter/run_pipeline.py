import pandas
from d3m import exceptions
import json
from d3m.metadata import base as metadata_base, problem as base_problem
from d3m.metadata.pipeline import Pipeline
from d3m.metadata.pipeline_run import RuntimeEnvironment
from d3m.container.dataset import ComputeDigest
from d3m.runtime import get_metrics_from_problem_description, evaluate, get_pipeline, get_dataset


class RunPipeline:

    """
    In this function we define all the parameters needed to actually execute the pipeline.

    :param datasets_dir: a string denoting the base directory containing all the datasets. For example `/datasets`
    :param volumes_dir: a string denoting the volumes directory, used by the runtime.
    :param pipeline_path: a string containing the full path to the pipeline file to be used (JSON or YML file)
    :param problem_path: a string containing the path to the given problem
    :param output_path: an optional parameter specifying the location to place the finished pipeline_run file.  If it
        is empty no output path is used.
    """
    def __init__(self, datasets_dir: str, volumes_dir: str, pipeline_path: str,
                 problem_path: str, output_path: str=None):
        self.datasets_dir = datasets_dir
        self.volumes_dir = volumes_dir
        self.pipeline_path = pipeline_path
        self.data_pipeline_path = './experimenter/pipelines/fixed-split-tabular-split.yml'
        self.scoring_pipeline_path = './experimenter/pipelines/scoring.yml'
        self.output_path = output_path
        self.problem_path = problem_path
        self.problem_name = self.problem_path.split("/")[-1]

        self.run_args = {'pipeline': self.pipeline_path,
                         "scoring_pipeline": self.scoring_pipeline_path,
                         'data_pipeline': self.data_pipeline_path,
                         'data_split_file': '{}/{}_problem/dataSplits.csv'.
                             format(self.problem_path, self.problem_name),
                         'problem': '{}/{}_problem/problemDoc.json'.
                             format(self.problem_path, self.problem_name),
                         'inputs': ['{}/{}_dataset/datasetDoc.json'.
                             format(self.problem_path, self.problem_name)],
                         "context": metadata_base.Context.TESTING
                         }

    """
    This function is what actually executes the pipeline, splits it, and returns the final predictions and scores. 
    Note that this function is EXTREMELY simimlar to that of `_evaluate` in the Runtime code. The aforementioned
    function does not allow for returning the data, so it did not fit in the workflow.
    
    :param pipeline: the pipeline object to be run OR the path to the pipeline file to be used
    :param random_seed: the random seed that the runtime will use to evalutate the pipeline
    :returns results_list: a list containing, in order, the scores from the pipeline predictions, the fit pipeline_run 
        and the produce pipeline_run.
    """
    def run(self, pipeline=None, random_seed: int=0):

        arguments = self.run_args

        runtime_environment = RuntimeEnvironment()

        dataset_resolver = get_dataset

        context = metadata_base.Context[arguments["context"]]

        if type(pipeline) != Pipeline:
            pipeline = get_pipeline(
                arguments["pipeline"],
                strict_resolving=False,
                strict_digest=False,
                pipeline_search_paths=[],
                load_all_primitives=False
            )

        data_pipeline = get_pipeline(
            arguments["data_pipeline"],
            strict_resolving=False,
            strict_digest= False,
            pipeline_search_paths=[],
            load_all_primitives=False
        )
        scoring_pipeline = get_pipeline(
            arguments["scoring_pipeline"],
            strict_resolving=False,
            strict_digest=False,
            pipeline_search_paths=[],
            load_all_primitives=False
        )

        problem_description = base_problem.parse_problem_description(arguments["problem"])

        inputs = [
            dataset_resolver(
                input_uri,
                compute_digest=ComputeDigest[ComputeDigest.ONLY_IF_MISSING.name],
                strict_digest=False,
            )
            for input_uri in arguments['inputs']
        ]

        data_params = {}

        split_file = pandas.read_csv(
            arguments["data_split_file"],
            # We do not want to do any conversion of values at this point.
            # This should be done by primitives later on.
            dtype=str,
            # We always expect one row header.
            header=0,
            # We want empty strings and not NaNs.
            na_filter=False,
            encoding='utf8',
            low_memory=False,
            memory_map=True,
        )

        # We use just the "d3mIndex" column and ignore multi-key indices.
        # This works for now because it seems that every current multi-key
        # dataset in fact has an unique value in "d3mIndex" alone.
        # See: https://gitlab.datadrivendiscovery.org/MIT-LL/d3m_data_supply/issues/117
        # Hyper-parameter value has to be JSON-serialized.
        data_params['primary_index_values'] = json.dumps(
            list(split_file.loc[split_file['type'] == 'TEST']['d3mIndex']))


        metrics = get_metrics_from_problem_description(problem_description)

        try:
            results_list = evaluate(
                pipeline, data_pipeline, scoring_pipeline, problem_description, inputs, data_params, metrics,
                context=context, random_seed=random_seed,
                data_random_seed=random_seed,
                scoring_random_seed=random_seed,
                volumes_dir=self.volumes_dir,
                runtime_environment=runtime_environment,
            )
        except exceptions.PipelineRunError as error:
            print("ERROR: {}".format(error.pipeline_runs))
            raise error

        return results_list
