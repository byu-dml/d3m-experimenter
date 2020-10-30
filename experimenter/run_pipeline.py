import logging
import json

import pandas
from d3m.metadata import base as metadata_base, problem as base_problem
from d3m.metadata.pipeline import Pipeline
from d3m.metadata.pipeline_run import RuntimeEnvironment
from d3m.container.dataset import ComputeDigest
from d3m.runtime import (
    get_metrics_from_problem_description,
    get_metrics_from_list,
    evaluate,
    get_pipeline,
    get_dataset,
)

from experimenter.problem import ProblemReference

logger = logging.getLogger(__name__)


class RunPipeline:

    """
    In this function we define all the parameters needed to actually execute the
    pipeline.

    :param volumes_dir: a string denoting the volumes directory, used by the runtime.
    :param problem: the problem pipelines will be run on.
    :param output_path: an optional parameter specifying the location to place the
        finished pipeline_run file. If it is empty no output path is used.
    """

    def __init__(
        self, volumes_dir: str, problem: ProblemReference, output_path: str = None,
    random_seed: int = None):
        self.volumes_dir = volumes_dir
        self.data_pipeline_path = (
            "./experimenter/pipelines/fixed-split-tabular-split.yml"
        )
        self.scoring_pipeline_path = "./experimenter/pipelines/scoring.yml"
        self.output_path = output_path

        self.run_args = {
            "scoring_pipeline": self.scoring_pipeline_path,
            "data_pipeline": self.data_pipeline_path,
            "data_split_file": problem.data_splits_path,
            "problem": problem.problem_doc_path,
            "inputs": [problem.dataset_doc_path],
            "context": metadata_base.Context.PRODUCTION,
        }
        self.random_seed = random_seed

    def run(self, pipeline: Pipeline, metric_names: list = None) -> list:
        """
        This function is what actually executes the pipeline, splits it, and returns
        the final predictions and scores. Note that this function is EXTREMELY
        simimlar to that of `_evaluate` in the Runtime code. The aforementioned
        function does not allow for returning the data, so it did not fit in the
        workflow.
        
        :param pipeline: the pipeline object to be run OR the path to the pipeline file
            to be used
        :param metric_names: if provided, the pipeline will be scored against this custom
            list of metric names. See `d3m.metadata.problem.PerformanceMetric`
            for a list of possible values. If not provided, the metrics listed in the
            problem description will be used.
        :returns results_list: a list containing, in order, the scores from the pipeline
            predictions, the fit pipeline_run and the produce pipeline_run.
        """

        arguments = self.run_args
        #use the random seed if passed to run
        if (self.random_seed is None):
            runtime_environment = RuntimeEnvironment()
        else:
            runtime_environment = RuntimeEnvironment()

        dataset_resolver = get_dataset

        context = metadata_base.Context[arguments["context"]]

        data_pipeline = get_pipeline(
            arguments["data_pipeline"],
            strict_resolving=False,
            strict_digest=False,
            pipeline_search_paths=[],
            load_all_primitives=False,
        )
        scoring_pipeline = get_pipeline(
            arguments["scoring_pipeline"],
            strict_resolving=False,
            strict_digest=False,
            pipeline_search_paths=[],
            load_all_primitives=False,
        )

        problem_description = base_problem.parse_problem_description(
            arguments["problem"]
        )

        inputs = [
            dataset_resolver(
                input_uri,
                compute_digest=ComputeDigest[ComputeDigest.ONLY_IF_MISSING.name],
                strict_digest=False,
            )
            for input_uri in arguments["inputs"]
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
            encoding="utf8",
            low_memory=False,
            memory_map=True,
        )

        # We use just the "d3mIndex" column and ignore multi-key indices.
        # This works for now because it seems that every current multi-key
        # dataset in fact has an unique value in "d3mIndex" alone.
        # See: https://gitlab.datadrivendiscovery.org/MIT-LL/d3m_data_supply/issues/117
        # Hyper-parameter value has to be JSON-serialized.
        data_params["primary_index_values"] = json.dumps(
            list(split_file.loc[split_file["type"] == "TEST"]["d3mIndex"])
        )

        if metric_names is None:
            metrics = get_metrics_from_problem_description(problem_description)
        else:
            metrics = get_metrics_from_list(metric_names)
        if (self.random_seed is None):
            all_scores, all_results = evaluate(
                pipeline,
                inputs,
                data_pipeline=data_pipeline,
                scoring_pipeline=scoring_pipeline,
                problem_description=problem_description,
                data_params=data_params,
                metrics=metrics,
                context=context,
                volumes_dir=self.volumes_dir,
                runtime_environment=runtime_environment,
            )
        #for seed change
        else:
            logger.warning('Random Seed: {}'.format(self.random_seed))
            all_scores, all_results = evaluate(
                pipeline,
                inputs,
                data_pipeline=data_pipeline,
                scoring_pipeline=scoring_pipeline,
                problem_description=problem_description,
                data_params=data_params,
                metrics=metrics,
                context=context,
                volumes_dir=self.volumes_dir,
                runtime_environment=runtime_environment,
                random_seed=self.random_seed,
                scoring_random_seed=self.random_seed, 
                data_random_seed=self.random_seed
            )
        

        all_results.check_success()

        return all_scores, all_results
