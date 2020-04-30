import json
import os
import typing
import unittest

import d3m.exceptions as d3m_exceptions
from d3m.metadata import pipeline as pipeline_module
from experimenter.validation import *


class TestSchemaValidation(unittest.TestCase):
    def setUp(self):
        self.pipeline_path = os.path.join(os.getcwd(), "experimenter/pipelines")

    def test_valid_pipeline_run_schema(self):
        with open(
            os.path.join(self.pipeline_path, "valid_pipeline_run.json"), "r"
        ) as file:
            pipeline_run = json.load(file)
        validated = validate_pipeline_run(pipeline_run)
        self.assertTrue(
            validated, "The schema validation FAILED, when it should have PASSED"
        )

    def test_invalid_pipeline_run_schema(self):
        with open(
            os.path.join(self.pipeline_path, "invalid_pipeline_run.json"), "r"
        ) as file:
            pipeline_run = json.load(file)
        validated = validate_pipeline_run(pipeline_run)
        self.assertFalse(
            validated, "The schema validation PASSED, when it should have FAILED"
        )

    def test_valid_pipeline_schema(self):
        with open(
            os.path.join(self.pipeline_path, "bagging_classification.json"), "r"
        ) as file:
            pipeline_to_check = pipeline_module.Pipeline.from_json(string_or_file=file)
        try:
            pipeline_to_check.check()
        except Exception as error:
            self.fail(
                "Valid pipeline schema failed to validate because of {}".format(error)
            )

    def test_invalid_pipeline_schema(self):
        try:
            with open(
                os.path.join(self.pipeline_path, "invalid_pipeline.json"), "r"
            ) as file:
                pipeline_to_check = pipeline_module.Pipeline.from_json(
                    string_or_file=file
                )
                self.fail(
                    "Invalid pipeline schema validated when it should have FAILED"
                )
        except Exception:
            pass
