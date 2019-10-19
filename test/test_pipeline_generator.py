import sys
import unittest

from experimenter.experimenter import Experimenter
from experimenter.constants import TEST_DATASET_PATHS


class PipelineGenerationTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.datasets_dir = '/datasets'
        cls.seed_problem_directory = ['seed_datasets_current']

    # @classmethod
    def setUp(self):
        volumes_dir = '/volumes'
        meta_file_path = './.meta'
        models = {'classification': ['d3m.primitives.classification.gaussian_naive_bayes.SKlearn']}
        preprocessors = []  # give no preprocessors
        self.experimenter_driver = Experimenter(
            self.datasets_dir, volumes_dir,
            input_problem_directory=self.seed_problem_directory,
            input_models=models,
            input_preprocessors=preprocessors,
            generate_problems=True,
        )

    def test_get_classification_problems(self):
        # 196_auto_mpg is regression
        known_seed_classification_problems_test = set({
            TEST_DATASET_PATHS['38_sick'],
            TEST_DATASET_PATHS['1491_one_hundred_plant_margins']
        })

        found_problems = set(self.experimenter_driver.problems['classification'])
        for known_problem in known_seed_classification_problems_test:
            self.assertTrue(
                known_problem in found_problems,
                'known problem {} not found'.format(known_problem)
            )
    
    def test_basic_pipeline_structure(self):
        num_pipeline_steps = 8  # DatasetToDataFrame/
                                # ExtractSemanticTypes(attributes)/
                                # OneHotEncoder/
                                # ColumnParser/SKImputer/
                                # ExtractSemanticTypes(targets)/
                                # SKGaussianNB/ConstructPredictions
        dataset_to_dataframe = 'd3m.primitives.data_transformation.dataset_to_dataframe.Common'
        construct_predictions = 'd3m.primitives.data_transformation.construct_predictions.DataFrameCommon'

        print("Testing that the pipelines are what they should be...")
        # should only make one pipeline with no preprocessor

        self.assertEqual(
            1, len(self.experimenter_driver.generated_pipelines['classification']),
            'Expected 1 pipeline to be generated, but got {}'.format(
                len(self.experimenter_driver.generated_pipelines['classification'])
            )
        )
        generated_pipelines = self.experimenter_driver.generated_pipelines['classification'][0].to_json_structure()
        # make sure there are the normal number of steps in the pipeline
        self.assertEqual(len(generated_pipelines['steps']), num_pipeline_steps)
        self.assertEqual(generated_pipelines['steps'][0]['primitive']['python_path'], dataset_to_dataframe)
        self.assertEqual(generated_pipelines['steps'][-1]['primitive']['python_path'], construct_predictions)
