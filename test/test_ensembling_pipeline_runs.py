import typing
import unittest
from experimenter.experimenter import *
from experimenter.constants import models, bulletproof_preprocessors
from d3m import runtime as runtime_module
from d3m.metadata import pipeline as pipeline_module
from experimenter.run_pipeline import RunPipeline
from experimenter.experiments.ensemble import EnsembleArchitectureExperimenter
from test.config import test_problem_reference


def get_pipeline(
    pipeline_path: str,
    *,
    strict_resolving: bool = False,
    strict_digest: bool = False,
    pipeline_search_paths: typing.Sequence[str] = None,
    respect_environment_variable: bool = True,
    load_all_primitives: bool = False,
    resolver_class: typing.Type[pipeline_module.Resolver] = pipeline_module.Resolver,
    pipeline_class: typing.Type[pipeline_module.Pipeline] = pipeline_module.Pipeline,
):
    return runtime_module.get_pipeline(
        pipeline_path=pipeline_path,
        strict_resolving=strict_resolving,
        strict_digest=strict_digest,
        pipeline_search_paths=pipeline_search_paths,
        respect_environment_variable=respect_environment_variable,
        load_all_primitives=load_all_primitives,
        resolver_class=resolver_class,
        pipeline_class=pipeline_class,
    )


class TestEnsemblingPipelineRuns(unittest.TestCase):

    TEST_RESULTS_PATH = "./test_results.yml"

    def setUp(self):
        self.datasets_dir = "/datasets"
        self.volumes_dir = "/volumes"
        self.pipeline_path = "./experimenter/pipelines/ensemble_test.json"
        self.data_pipeline_path = (
            "./experimenter/pipelines/fixed-split-tabular-split.yml"
        )
        self.scoring_pipeline_path = "./experimenter/pipelines/scoring.yml"
        self.experiment = EnsembleArchitectureExperimenter()
        self.preprocessors = bulletproof_preprocessors
        self.models = models
        self.problem_type = test_problem_reference.problem_type
        self.problem_path = test_problem_reference.path

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.TEST_RESULTS_PATH)
        except OSError:
            pass

    def test_experimenter_run_works_and_generates_random(self):
        generated_pipelines = self.experiment._generate_k_ensembles(
            k_ensembles=3,
            n_preprocessors=2,
            preprocessors=self.preprocessors,
            models=self.models,
            n_generated_pipelines=1,
            same_model=False,
            same_preprocessor_order=False,
            problem_type=self.problem_type,
        )
        pipeline_to_run = generated_pipelines[self.problem_type][0]
        self.run_experimenter_from_pipeline(self.problem_path, pipeline_to_run)

    def test_experimenter_run_works_and_generates_fixed(self):
        model_map = {
            "classification": "d3m.primitives.classification.random_forest.SKlearn",
            "regression": "d3m.primitives.regression.random_forest.SKlearn",
        }
        generated_pipelines = self.experiment._generate_k_ensembles(
            k_ensembles=3,
            n_preprocessors=2,
            preprocessors=self.preprocessors,
            models=self.models,
            n_generated_pipelines=1,
            same_model=True,
            same_preprocessor_order=False,
            problem_type=self.problem_type,
            model=model_map[self.problem_type],
        )
        pipeline_to_run = generated_pipelines[self.problem_type][0]
        self.run_experimenter_from_pipeline(self.problem_path, pipeline_to_run)

    def test_experimenter_run_works_and_generates_LARGE(self):
        generated_pipelines = self.experiment._generate_k_ensembles(
            k_ensembles=6,
            n_preprocessors=4,
            preprocessors=self.preprocessors,
            models=self.models,
            n_generated_pipelines=1,
            same_model=False,
            same_preprocessor_order=False,
            problem_type=self.problem_type,
        )
        pipeline_to_run = generated_pipelines[self.problem_type][0]
        self.run_experimenter_from_pipeline(self.problem_path, pipeline_to_run)

    def run_experimenter_from_pipeline(self, problem_path, pipeline_to_run=None):
        if pipeline_to_run is None:
            # load pipeline
            with open(self.pipeline_path, "r") as file:
                pipeline_to_run = pipeline_module.Pipeline.from_json(
                    string_or_file=file
                )

        # run our system
        run_pipeline = RunPipeline(
            datasets_dir=self.datasets_dir,
            volumes_dir=self.volumes_dir,
            problem_path=self.problem_path,
        )
        scores_test, _ = run_pipeline.run(pipeline=pipeline_to_run)
        # the value of score is in the first document in the first index
        score = scores_test[0]["value"][0]
        return score
