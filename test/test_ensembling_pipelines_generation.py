import unittest
from experimenter.experimenter import *
from experimenter.database_communication import primitive_list_from_pipeline_json
from experimenter.constants import models, bulletproof_preprocessors
from experimenter.experiments.ensemble import EnsembleArchitectureExperimenter


class TestEnsemblingPipelinesGeneration(unittest.TestCase):

    TEST_RESULTS_PATH = './test_results.yml'

    def setUp(self):
        self.datasets_dir = "/datasets"
        self.volumes_dir = "/volumes"
        self.pipeline_path = './experimenter/pipelines/bagging_classification.json'
        self.data_pipeline_path = './experimenter/pipelines/fixed-split-tabular-split.yml'
        self.scoring_pipeline_path = './experimenter/pipelines/scoring.yml'
        # initialize the experimenter
        self.experiment = EnsembleArchitectureExperimenter()
        self.preprocessors = bulletproof_preprocessors
        self.models = models

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.TEST_RESULTS_PATH)
        except OSError:
            pass

    def test_experimenter_can_generate_basic(self):
        # generate the pipelines
        generated_pipelines = self.experiment._generate_k_ensembles(k_ensembles=3, n_preprocessors=1,
                                                                        preprocessors=self.preprocessors,
                                                                        models=self.models,
                                                                        n_generated_pipelines=1, same_model=False,
                                                                        same_preprocessor_order=False,
                                                                        problem_type="classification")
        self.assertEqual(1, len(generated_pipelines["classification"]))
        # validate the pipeline
        generated_pipelines["classification"][0].check()

    def test_experimenter_can_generate_all_types(self):
        # generate the pipelines
        generated_pipelines = self.experiment._generate_k_ensembles(k_ensembles=3, n_preprocessors=1,
                                                                        preprocessors=self.preprocessors,
                                                                        models=self.models,
                                                                        n_generated_pipelines=1, same_model=False,
                                                                        same_preprocessor_order=False,
                                                                        problem_type="all")
        self.assertEqual(1, len(generated_pipelines["classification"]))
        self.assertEqual(1, len(generated_pipelines["regression"]))

        # validate the pipeline
        generated_pipelines["classification"][0].check()
        generated_pipelines["regression"][0].check()

    def test_experimenter_can_generate_multiples(self):
        # generate the pipelines
        generated_pipelines = self.experiment._generate_k_ensembles(k_ensembles=3, n_preprocessors=1,
                                                                        preprocessors=self.preprocessors,
                                                                        models=self.models,
                                                                        n_generated_pipelines=10, same_model=False,
                                                                        same_preprocessor_order=False,
                                                                        problem_type="classification")
        self.assertEqual(10, len(generated_pipelines["classification"]))
        # validate the pipelines
        for pipeline in generated_pipelines["classification"]:
            pipeline.check()

    # TODO: add a command line argument to allow this to happen in the Experimenter generate pipelines section
    # def test_experimenter_can_generate_multiple_preprocessors(self):
    #     num_preprocessors = 5
    #     num_ensembles = 3
    #     # generate the pipelines
    #     generated_pipelines = self.experiment._generate_k_ensembles(k_ensembles=num_ensembles, n_preprocessors=num_preprocessors,
    #                                                                     preprocessors=self.preprocessors,
    #                                                                     models=self.models,
    #                                                                     n_generated_pipelines=1, same_model=False,
    #                                                                     same_preprocessor_order=True,
    #                                                                     problem_type="classification")
    #     self.assertEqual(1, len(generated_pipelines["classification"]))

    #     primitives = primitive_list_from_pipeline_json(generated_pipelines["classification"][0].to_json_structure())
    #     preprocessor_count = 0
    #     for primitive in primitives:
    #         if primitive in self.preprocessors:
    #             preprocessor_count += 1
    #     self.assertEqual(num_preprocessors * num_ensembles, preprocessor_count, "The expected number of preprocessors was {} but we got"
    #                                                             "{}".format(num_ensembles * num_preprocessors, preprocessor_count))

    def test_experimenter_can_generate_same_models(self):
        num_models = 5
        model_python_path = 'd3m.primitives.classification.gaussian_naive_bayes.SKlearn'
        # generate the pipelines
        generated_pipelines = self.experiment._generate_k_ensembles(k_ensembles=num_models, n_preprocessors=1,
                                                                   preprocessors=self.preprocessors,
                                                                   models=self.models,
                                                                   n_generated_pipelines=1, same_model=True,
                                                                   same_preprocessor_order=True,
                                                                   model=model_python_path,
                                                                   problem_type="classification")
        self.assertEqual(1, len(generated_pipelines["classification"]))

        primitives = primitive_list_from_pipeline_json(generated_pipelines["classification"][0].to_json_structure())
        num_models_used = sum(1 for p in primitives if p == model_python_path)
        self.assertEqual(num_models_used, num_models)

    def test_experimenter_has_correct_input(self):
        # Should fail
        try:
            generated_pipelines = self.experiment._generate_k_ensembles(k_ensembles=3, n_preprocessors=1,
                                                                       preprocessors=self.preprocessors,
                                                                       models=self.models,
                                                                       n_generated_pipelines=10, same_model=True,
                                                                       same_preprocessor_order=False,
                                                                       problem_type="classification")
            self.fail("An error was supposed to be thrown, but was not. Same model was true with no models given")
        except Exception:
            pass

    def test_experimenter_has_correct_input_model_length(self):
        # Should fail
        try:
            generated_pipelines = self.experiment._generate_k_ensembles(k_ensembles=3, n_preprocessors=1,
                                                                       preprocessors=self.preprocessors,
                                                                       models=self.models,
                                                                       n_generated_pipelines=10, same_model=True,
                                                                       same_preprocessor_order=False,
                                                                       problem_type="classification",
                                                                       model=["Classifier1", "Classifier2"])
            self.fail("An error was supposed to be thrown, but was not. Same model was true with more than o"
                      "ne model given")
        except Exception:
            pass


