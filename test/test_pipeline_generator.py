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
            '/datasets/seed_datasets_current/LL1_ElectricDevices', 
            '/datasets/seed_datasets_current/LL1_ArrowHead',
            '/datasets/seed_datasets_current/LL1_HandOutlines',
            '/datasets/seed_datasets_current/124_174_cifar10',
            '/datasets/seed_datasets_current/LL1_ECG200',
            '/datasets/seed_datasets_current/LL1_TXT_CLS_airline_opinion',
            '/datasets/seed_datasets_current/LL1_50words',
            '/datasets/seed_datasets_current/uu6_hepatitis',
            '/datasets/seed_datasets_current/LL1_Adiac',
            '/datasets/seed_datasets_current/LL1_multilearn_emotions',
            '/datasets/seed_datasets_current/LL1_FaceFour',
            '/datasets/seed_datasets_current/uu_101_object_categories',
            '/datasets/seed_datasets_current/uu7_pima_diabetes',
            '/datasets/seed_datasets_current/31_urbansound',
            '/datasets/seed_datasets_current/uu10_posts_3',
            '/datasets/seed_datasets_current/124_188_usps',
            '/datasets/seed_datasets_current/LL1_Haptics',
            '/datasets/seed_datasets_current/LL1_OSULeaf',
            '/datasets/seed_datasets_current/LL1_CinC_ECG_torso',
            '/datasets/seed_datasets_current/124_214_coil20',
            '/datasets/seed_datasets_current/299_libras_move',
            '/datasets/seed_datasets_current/loan_status',
            '/datasets/seed_datasets_current/LL1_Meat',
            '/datasets/seed_datasets_current/32_fma',
            '/datasets/seed_datasets_current/LL1_ItalyPowerDemand',
            '/datasets/seed_datasets_current/LL1_FordA',
            '/datasets/seed_datasets_current/LL1_VID_UCF11',
            '/datasets/seed_datasets_current/LL1_TXT_CLS_apple_products_sentiment',
            '/datasets/seed_datasets_current/LL1_TXT_CLS_3746_newsgroup',
            '/datasets/seed_datasets_current/LL1_Cricket_Y',
            '/datasets/seed_datasets_current/LL1_FISH'
        ])

        found_problems = set(self.experimenter_driver.problems['classification'])
        for known_problem in known_seed_classification_problems:
            self.assertTrue(
                known_problem in found_problems,
                'known problem {} not found'.format(known_problem)
            )
    
    def test_basic_pipeline_structure(self):

        num_pipeline_steps = 6  # DatasetToDataFrame/ColumnParser/SKImputer/ExtractSemanticTypes/
                                # SKGaussianNB/ConstructPredictions
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
        self.assertEqual(generated_pipelines['steps'][5]['primitive']['python_path'], pipeline_step_four)
