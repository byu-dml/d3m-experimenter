import pandas
from d3m import exceptions
import json
from d3m.metadata import base as metadata_base, pipeline as pipeline_module, problem as base_problem
from d3m.container.dataset import Dataset
from d3m.runtime import get_metrics_from_problem_description, evaluate


class RunPipeline:

    def __init__(self, datasets_dir: str, volumes_dir: str, pipeline_path: str,
                 problem_path: str, output_path: str=None):
        self.datasets_dir = datasets_dir
        self.volumes_dir = volumes_dir
        self.pipeline_path = pipeline_path
        self.output_path = output_path
        self.problem_path = problem_path
        self.problem_name = self.problem_path.split("/")[-1]

    def run(self, problem_path, pipeline=None, random_seed: int=0):
        # Loading problem description.
        problem_description = base_problem.parse_problem_description(self.problem_path +
                                                                     "/{}_problem/problemDoc.json".format(self.problem_name))
        # Loading dataset.
        dataset_path = 'file://{uri}'.format(uri=self.problem_path +
                                                 '/{}_dataset/datasetDoc.json'.format(self.problem_name))
        dataset = Dataset.load(dataset_uri=dataset_path)

        # Loading splits.
        split_file_path = 'file://{uri}'.format(uri=self.problem_path  +
                                                    '/{}_problem/dataSplits.csv'.format(self.problem_name))

        split_file = pandas.read_csv(
            split_file_path,
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

        # Code from line 2067 of Runtime.py - used in the runtime command line interface.  See for more details
        data_params = {}
        data_params['primary_index_values'] = json.dumps(
            list(split_file.loc[split_file['type'] == 'TEST']['d3mIndex']))

        metrics = get_metrics_from_problem_description(problem_description)

        if pipeline is None:
            # Loading pipeline description file.
            with open('pipe.yml', 'r') as file:
                pipeline_to_run = pipeline_module.Pipeline.from_yaml(string_or_file=file)
        else:
            # use given pipeline
            pipeline_to_run = pipeline

        with open('experimenter/pipeline/train-test-tabular-split.yml', 'r') as file:
            data_pipeline = pipeline_module.Pipeline.from_yaml(string_or_file=file)

        with open('experimenter/pipeline/scoring.yml', 'r') as file:
            scoring_pipeline = pipeline_module.Pipeline.from_yaml(string_or_file=file)

        results_list = ""

        results_list = evaluate(
            pipeline_to_run, data_pipeline, scoring_pipeline, problem_description, [dataset], data_params, metrics,
            context=metadata_base.Context.TESTING, random_seed=random_seed,
            data_random_seed=random_seed,
            scoring_random_seed=random_seed,
            volumes_dir="/volumes",  # TODO: make variable
        )

        print(results_list)

        return results_list
