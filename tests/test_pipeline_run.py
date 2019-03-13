import argparse
import unittest

import yaml

from d3m.runtime import handler, configure_parser
from d3m.metadata import pipeline as pipeline_module
from experimenter.pipeline.run_pipeline import RunPipeline



class PipelineGenerationTestCase(unittest.TestCase):

    # @classmethod
    # def setUpClass(cls):
    #     cls.datasets_dir = sys.argv[1]  # TODO: move to .env
    #     cls.seed_problem_directory = ['/seed_datasets_current/']

    # @classmethod
    def setUp(self):
        self.datasets_dir = "/datasets"
        self.volumes_dir = "/volumes"
        self.pipeline_path = 'tests/testing_pipelines/test_bagging_classification.json'

    def test_run_mice_protein_problem(self):
        problem_path = "/datasets/seed_datasets_current/4550_MiceProtein/"

        # Check that D3M is working and get results
        parser = argparse.ArgumentParser(description="Run D3M pipelines with default hyper-parameters.")
        configure_parser(parser)
        test_args = ['evaluate',
                     '-p', self.pipeline_path,
                     '-n', 'tests/testing_pipelines/scoring.yml',
                     '-d', 'tests/testing_pipelines/fixed-split-tabular-split.yml',
                     '--data-split-file',
                     '/datasets/seed_datasets_current/4550_MiceProtein/4550_MiceProtein_problem/dataSplits.csv',
                     '-r', '/datasets/seed_datasets_current/4550_MiceProtein/4550_MiceProtein_problem/problemDoc.json',
                     '-i', '/datasets/seed_datasets_current/4550_MiceProtein/4550_MiceProtein_dataset/datasetDoc.json',
                     '-O', 'test_results.yml']

        arguments = parser.parse_args(args=test_args)
        handler(arguments, parser)
        quit(0)
        import pdb; pdb.set_trace()
        # get results form output file
        with open('test_results.yml', 'r') as file:
            # grab the second document, containing the scores
            d3m_results = list(yaml.load_all(file))
            # get the F1-Macro
            d3m_results = d3m_results["run"]["results"]["predictions"]["scores"]["value"]

        # Check our system
        # load pipeline
        with open(self.pipeline_path, 'r') as file:
            pipeline_to_run = pipeline_module.Pipeline.from_json(string_or_file=file)

        # run our system
        run_pipeline = RunPipeline(self.datasets_dir, self.volumes_dir, self.pipeline_path, problem_path)
        results_test = run_pipeline.run(problem_path, pipeline_to_run)[0]
        score = results_test[0]

        # compare systems
        self.assertEqual(d3m_results, score, "Our results from the experimenter were {} while D3M's results were {}".
                         format(d3m_results, score))


