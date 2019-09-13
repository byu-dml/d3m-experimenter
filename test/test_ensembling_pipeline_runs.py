import typing
import unittest
from experimenter.experimenter import *
from experimenter.constants import models, preprocessors
from d3m import runtime as runtime_module
from d3m.metadata import pipeline as pipeline_module
from experimenter.run_pipeline import RunPipeline


def get_pipeline(
    pipeline_path: str, *, strict_resolving: bool = False,
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

    TEST_RESULTS_PATH = './test_results.yml'

    def setUp(self):
        self.datasets_dir = "/datasets"
        self.volumes_dir = "/volumes"
        self.pipeline_path = './experimenter/pipelines/ensemble_test.json'
        self.data_pipeline_path = './experimenter/pipelines/fixed-split-tabular-split.yml'
        self.scoring_pipeline_path = './experimenter/pipelines/scoring.yml'
        self.experiment = Experimenter(self.datasets_dir, self.volumes_dir, generate_pipelines=False,
                                       generate_problems=False, generate_automl_pipelines=False)
        self.preprocessors = preprocessors
        self.models = models

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.TEST_RESULTS_PATH)
        except OSError:
            pass

    def test_experimenter_run_works_from_pipeline(self):
        problem_path = "/datasets/seed_datasets_current/185_baseball"
        self.run_experimenter_from_pipeline(problem_path)

    def test_experimenter_run_works_and_generates_random(self):
        generated_pipelines = self.experiment.generate_k_ensembles(k_ensembles=3, p_preprocessors=2,
                                                                   n_generated_pipelines=1, same_model=False,
                                                                   same_preprocessor_order=False,
                                                                   problem_type="classification")
        pipeline_to_run = generated_pipelines["classification"][0]
        problem_path = "/datasets/seed_datasets_current/185_baseball"
        self.run_experimenter_from_pipeline(problem_path, pipeline_to_run)

    def test_experimenter_run_works_and_generates_fixed(self):
        model = "d3m.primitives.classification.random_forest.SKlearn"
        generated_pipelines = self.experiment.generate_k_ensembles(k_ensembles=3, p_preprocessors=2,
                                                                   n_generated_pipelines=1, same_model=True,
                                                                   same_preprocessor_order=False,
                                                                   problem_type="classification",
                                                                   model=model)
        pipeline_to_run = generated_pipelines["classification"][0]
        problem_path = "/datasets/seed_datasets_current/185_baseball"
        self.run_experimenter_from_pipeline(problem_path, pipeline_to_run)

    def test_experimenter_run_works_and_generates_LARGE(self):
        self.fail("testing")
        generated_pipelines = self.experiment.generate_k_ensembles(k_ensembles=6, p_preprocessors=4,
                                                                   n_generated_pipelines=1, same_model=False,
                                                                   same_preprocessor_order=False,
                                                                   problem_type="classification")
        pipeline_to_run = generated_pipelines["classification"][0]
        problem_path = "/datasets/seed_datasets_current/185_baseball"
        self.run_experimenter_from_pipeline(problem_path, pipeline_to_run)

    def run_experimenter_from_pipeline(self, problem_path, pipeline_to_run=None):
        if pipeline_to_run is None:
            # load pipeline
            with open(self.pipeline_path, 'r') as file:
                pipeline_to_run = pipeline_module.Pipeline.from_json(string_or_file=file)

        # run our system
        run_pipeline = RunPipeline(datasets_dir=self.datasets_dir, volumes_dir=self.volumes_dir,
                                   problem_path=problem_path)
        scores_test, _ = run_pipeline.run(pipeline=pipeline_to_run)
        # the value of score is in the first document in the first index
        score = scores_test[0]["value"][0]
        return score
