import sys
import unittest

from experimenter.experimenter import Experimenter
from test.config import TEST_PROBLEM_REFERENCES


class PipelineGenerationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datasets_dir = "/datasets"
        cls.seed_problem_directory = "seed_datasets_current"

    # @classmethod
    def setUp(self):
        volumes_dir = "/volumes"
        models = {
            "classification": [
                "d3m.primitives.classification.gaussian_naive_bayes.SKlearn"
            ]
        }
        preprocessors = []  # give no preprocessors
        self.experimenter_driver = Experimenter(
            self.datasets_dir,
            volumes_dir,
            input_problem_directories=[self.seed_problem_directory],
            input_models=models,
            input_preprocessors=preprocessors,
            generate_problems=True,
        )

    def test_get_classification_problems(self):
        known_seed_classification_problems_test = set(
            [
                ref
                for ref in TEST_PROBLEM_REFERENCES.values()
                if ref.problem_type == "classification"
            ]
        )

        found_problem_paths = set(self.experimenter_driver.problems["classification"])
        for known_problem in known_seed_classification_problems_test:
            self.assertTrue(
                known_problem.path in found_problem_paths,
                f"known problem {known_problem.name} not found at path {known_problem.path}\nknown paths: {found_problem_paths}",
            )

    def test_get_regression_problems(self):
        known_seed_regression_problems_test = set(
            [
                ref
                for ref in TEST_PROBLEM_REFERENCES.values()
                if ref.problem_type == "regression"
            ]
        )

        found_problem_paths = set(self.experimenter_driver.problems["regression"])
        for known_problem in known_seed_regression_problems_test:
            self.assertTrue(
                known_problem.path in found_problem_paths,
                f"known problem {known_problem.name} not found at path {known_problem.path}\nknown paths: {found_problem_paths}",
            )

    def test_basic_pipeline_structure(self):
        # DatasetToDataFrame ->
        # Profiler ->
        # ExtractSemanticTypes(targets) ->
        # ColumnParser(targets) ->
        # ExtractSemanticTypes(attributes) ->
        # ColumnParser(attributes) ->
        # BYUImputer ->
        # OneHotEncoder ->
        # SKGaussianNB ->
        # ConstructPredictions
        num_pipeline_steps = 10
        dataset_to_dataframe = (
            "d3m.primitives.data_transformation.dataset_to_dataframe.Common"
        )
        construct_predictions = (
            "d3m.primitives.data_transformation.construct_predictions.Common"
        )

        print("Testing that the pipelines are what they should be...")
        # should only make one pipeline with no preprocessor

        self.assertEqual(
            1,
            len(self.experimenter_driver.generated_pipelines["classification"]),
            "Expected 1 pipeline to be generated, but got {}".format(
                len(self.experimenter_driver.generated_pipelines["classification"])
            ),
        )
        generated_pipeline = self.experimenter_driver.generated_pipelines[
            "classification"
        ][0].to_json_structure()
        # make sure there are the normal number of steps in the pipeline
        self.assertEqual(len(generated_pipeline["steps"]), num_pipeline_steps)
        self.assertEqual(
            generated_pipeline["steps"][0]["primitive"]["python_path"],
            dataset_to_dataframe,
        )
        self.assertEqual(
            generated_pipeline["steps"][-1]["primitive"]["python_path"],
            construct_predictions,
        )
