import argparse
import os
import typing
import unittest
import yaml

from d3m import runtime as runtime_module
from d3m.cli import runtime_handler, runtime_configure_parser
from d3m.runtime import get_pipeline
from d3m.metadata import pipeline as pipeline_module

from experimenter.problem import ProblemReference
from test.config import TEST_PROBLEM_REFERENCES
from test.utils import run_experimenter_from_pipeline


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


class TestExecutingPipelines(unittest.TestCase):

    TEST_RESULTS_PATH = "./test_results.yml"

    def setUp(self):
        self.volumes_dir = "/volumes"
        self.pipeline_path = "./experimenter/pipelines/bagging_classification.json"
        self.pipeline = pipeline_module.Pipeline.from_json(
            string_or_file=open(self.pipeline_path, "r")
        )
        self.data_pipeline_path = (
            "./experimenter/pipelines/fixed-split-tabular-split.yml"
        )
        self.scoring_pipeline_path = "./experimenter/pipelines/scoring.yml"
        self.problem_ref = TEST_PROBLEM_REFERENCES[
            "1491_one_hundred_plants_margin_MIN_METADATA"
        ]

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.TEST_RESULTS_PATH)
        except OSError:
            pass

    def test_d3m_runtime_works(self):
        self.run_d3m(self.problem_ref)

    def test_experimenter_run_works_from_pipeline(self):
        run_experimenter_from_pipeline(self.pipeline, problem=self.problem_ref)

    def test_systems_output_equal(self):
        # run both systems
        experimenter_score = run_experimenter_from_pipeline(
            self.pipeline, problem=self.problem_ref
        )
        self.run_d3m(self.problem_ref)

        # get results from d3m output file
        with open(self.TEST_RESULTS_PATH, "r") as file:
            # grab the second document, containing the scores
            d3m_score = list(yaml.load_all(file))
            # get the F1-Macro from the first document
            d3m_score = d3m_score[1]["run"]["results"]["scores"][0]["value"]

        # compare systems
        self.assertEqual(
            d3m_score,
            experimenter_score,
            "Our results from the experimenter were {} while D3M's results were {}".format(
                d3m_score, experimenter_score
            ),
        )

    def run_d3m(self, problem: ProblemReference):
        # Check that D3M is working and get results
        parser = argparse.ArgumentParser(
            description="Run D3M pipelines with default hyper-parameters."
        )
        runtime_configure_parser(parser)
        test_args = [
            "evaluate",
            "-p",
            self.pipeline_path,
            "-n",
            self.scoring_pipeline_path,
            "-d",
            self.data_pipeline_path,
            "--data-split-file",
            problem.data_splits_path,
            "-r",
            problem.problem_doc_path,
            "-i",
            problem.dataset_doc_path,
            "-O",
            self.TEST_RESULTS_PATH,
        ]

        arguments = parser.parse_args(args=test_args)

        runtime_handler(arguments, parser, pipeline_resolver=get_pipeline)
