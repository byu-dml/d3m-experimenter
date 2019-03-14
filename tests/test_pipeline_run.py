import argparse
import os
import unittest
import yaml
from d3m.runtime import handler, configure_parser
from d3m.metadata import pipeline as pipeline_module
from experimenter.pipeline.run_pipeline import RunPipeline


class TestExecutingPipelines(unittest.TestCase):

    TEST_RESULTS_PATH = './test_results.yml'

    def setUp(self):
        self.datasets_dir = "/datasets"
        self.volumes_dir = "/volumes"
        self.pipeline_path = 'tests/testing_pipelines/test_bagging_classification.json'

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.TEST_RESULTS_PATH)
        except OSError:
            pass

    def test_d3m_runtime_works(self):
        problem_path = "/datasets/seed_datasets_current/185_baseball"
        problem_name = problem_path.split("/")[-1]
        self.run_d3m(problem_name)

    def test_experimenter_run_works_from_file(self):
        problem_path = "/datasets/seed_datasets_current/185_baseball"
        self.run_experimenter_from_file(problem_path)

    def test_experimenter_run_works_from_pipeline(self):
        problem_path = "/datasets/seed_datasets_current/185_baseball"
        self.run_experimenter_from_pipeline(problem_path)

    def test_systems_output_equal(self):
        problem_path = "/datasets/seed_datasets_current/185_baseball"
        problem_name = problem_path.split("/")[-1]

        # run both systems
        experimenter_score = self.run_experimenter_from_file(problem_path)
        self.run_d3m(problem_name)

        # get results from d3m output file
        with open(self.TEST_RESULTS_PATH, 'r') as file:
            # grab the second document, containing the scores
            d3m_score = list(yaml.load_all(file))
            # get the F1-Macro from the first document
            d3m_score = d3m_score[1]["run"]["results"]["scores"][0]["value"]

        # compare systems
        self.assertEqual(d3m_score, experimenter_score,
                         "Our results from the experimenter were {} while D3M's results were {}".
                         format(d3m_score, experimenter_score))

    def run_d3m(self, problem_name):
        # Check that D3M is working and get results
        parser = argparse.ArgumentParser(description="Run D3M pipelines with default hyper-parameters.")
        configure_parser(parser)
        test_args = ['evaluate',
                     '-p', self.pipeline_path,
                     '-n', 'tests/testing_pipelines/scoring.yml',
                     '-d', 'tests/testing_pipelines/fixed-split-tabular-split.yml',
                     '--data-split-file',
                     '/datasets/seed_datasets_current/{}/{}_problem/dataSplits.csv'.
                         format(problem_name, problem_name),
                     '-r', '/datasets/seed_datasets_current/{}/{}_problem/problemDoc.json'.
                         format(problem_name, problem_name),
                     '-i', '/datasets/seed_datasets_current/{}/{}_dataset/datasetDoc.json'.
                         format(problem_name, problem_name),
                     '-O', self.TEST_RESULTS_PATH]

        arguments = parser.parse_args(args=test_args)
        handler(arguments, parser)

    def run_experimenter_from_file(self, problem_path):
        # load pipeline
        with open(self.pipeline_path, 'r') as file:
            pipeline_to_run = pipeline_module.Pipeline.from_json(string_or_file=file)

        # run our system
        run_pipeline = RunPipeline(self.datasets_dir, self.volumes_dir, self.pipeline_path, problem_path)
        results_test = run_pipeline.run(pipeline=pipeline_to_run)[0]
        # the value of score is in the first document in the first index
        score = results_test[0]["value"][0]
        return score

    def run_experimenter_from_pipeline(self, problem_path):
        # run our system
        run_pipeline = RunPipeline(self.datasets_dir, self.volumes_dir, self.pipeline_path, problem_path)
        results_test = run_pipeline.run()[0]
        # the value of score is in the first document in the first index
        score = results_test[0]["value"][0]
        return score
