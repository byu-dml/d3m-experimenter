import sys
import unittest

from experimenter.experimenter import Experimenter


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
            self.seed_problem_directory, models, preprocessors,
            generate_problems=True
        )

    def test_get_classification_problems(self):
        
        known_seed_classification_problems = set([
            '/datasets/seed_datasets_current/4550_MiceProtein',
            '/datasets/seed_datasets_current/1491_one_hundred_plants_margin',
            '/datasets/seed_datasets_current/LL0_1100_popularkids',
            '/datasets/seed_datasets_current/LL0_acled_reduced',
            '/datasets/seed_datasets_current/313_spectrometer',
            '/datasets/seed_datasets_current/uu4_SPECT',
            '/datasets/seed_datasets_current/LL0_acled',
            '/datasets/seed_datasets_current/uu5_heartstatlog',
            '/datasets/seed_datasets_current/185_baseball',
            '/datasets/seed_datasets_current/27_wordLevels',
            '/datasets/seed_datasets_current/38_sick',
            '/datasets/seed_datasets_current/57_hypothyroid',
            '/datasets/seed_datasets_current/32_wikiqa'
        ])

        found_problems = set(self.experimenter_driver.problems['classification'])

        for known_problem in known_seed_classification_problems:
            self.assertTrue(
                known_problem in found_problems,
                'known problem {} not found'.format(known_problem)
            )
    
    def test_basic_pipeline_structure(self):

        num_pipeline_steps = 5  # DatasetToDataFrame/ColumnParser/SKImputer/SKGaussianNB/ConstructPredictions
        pipeline_step_zero = 'd3m.primitives.data_transformation.dataset_to_dataframe.Common'
        pipeline_step_four = 'd3m.primitives.data_transformation.construct_predictions.DataFrameCommon'

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
        self.assertEqual(generated_pipelines['steps'][0]['primitive']['python_path'], pipeline_step_zero)
        self.assertEqual(generated_pipelines['steps'][4]['primitive']['python_path'], pipeline_step_four)
