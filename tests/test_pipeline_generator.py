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
        pipeline_path = './pipe.yml'
        meta_file_path = './.meta'
        models = {'classification': ['d3m.primitives.classification.gaussian_naive_bayes.SKlearn']}
        preprocessors = []  # give no preprocessors
        self.experimenter_driver = Experimenter(
            self.datasets_dir, volumes_dir, pipeline_path,
            self.seed_problem_directory, models, preprocessors,
            generate_problems=True
        )

    def test_get_classification_problems(self):
        
        seed_classification_problems = [
            '/datasets//seed_datasets_current/4550_MiceProtein',
            '/datasets//seed_datasets_current/1491_one_hundred_plants_margin',
            '/datasets//seed_datasets_current/LL1_726_TIDY_GPS_carpool_bus_service_rating_prediction',
            '/datasets//seed_datasets_current/LL0_1100_popularkids',
            '/datasets//seed_datasets_current/LL0_acled_reduced',
            '/datasets//seed_datasets_current/313_spectrometer',
            '/datasets//seed_datasets_current/uu4_SPECT',
            '/datasets//seed_datasets_current/66_chlorineConcentration',
            '/datasets//seed_datasets_current/LL0_acled',
            '/datasets//seed_datasets_current/185_baseball',
            '/datasets//seed_datasets_current/LL0_186_braziltourism',
            '/datasets//seed_datasets_current/27_wordLevels',
            '/datasets//seed_datasets_current/1567_poker_hand',
            '/datasets//seed_datasets_current/38_sick',
            '/datasets//seed_datasets_current/57_hypothyroid',
            '/datasets//seed_datasets_current/32_wikiqa'
        ]

        self.assertEqual(
            self.experimenter_driver.problems, seed_classification_problems,
            'Not all seed classification problems fetched correctly'
        )
    
    def test_basic_pipeline_structure(self):

        num_pipeline_steps = 6  # Denormalize/DatasetToDataFrame/ColumnParser/SKImputer/SKGaussianNB/Construct Predictions
        pipeline_step_zero = 'd3m.primitives.datasets.Denormalize'
        pipeline_step_fifth = 'd3m.primitives.data.ConstructPredictions'

        print("Testing that the pipelines are what they should be...")
        # should only make one pipeline with no preprocessor
        self.assertEqual(
            1, len(self.experimenter_driver.generated_pipelines),
            'Expected 1 pipeline to be generated, but got {}'.format(
                len(self.experimenter_driver.generated_pipelines)
            )
        )
        generated_pipelines = self.experimenter_driver.generated_pipelines[0].to_json_structure()
        # make sure there are the normal number of steps in the pipeline
        self.assertEqual(len(generated_pipelines['steps']), num_pipeline_steps)
        self.assertEqual(generated_pipelines['steps'][0]['primitive']['python_path'], pipeline_step_zero)
        self.assertEqual(generated_pipelines['steps'][5]['primitive']['python_path'], pipeline_step_fifth)
