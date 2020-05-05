import unittest

from experimenter.experiments.random import RandomArchitectureExperimenter
from experimenter.constants import models, bulletproof_preprocessors
from experimenter.pipeline_builder import EZPipeline
from test.config import test_problem_reference
from test.utils import run_experimenter_from_pipeline


class TestRandomPipelines(unittest.TestCase):

    # Test Methods

    def setUp(self):
        self.experiment = RandomArchitectureExperimenter()
        self.preprocessors = bulletproof_preprocessors
        self.models = models
        self.problem_type = test_problem_reference.problem_type

    def test_can_generate_pipeline(self) -> None:
        pipeline = self._generate_random_pipeline()
        # Make sure the pipeline is valid in D3M's eyes.
        pipeline.check()

    def test_can_run_pipeline(self) -> None:
        pipeline = self._generate_random_pipeline()
        run_experimenter_from_pipeline(pipeline, "wide+deep")

    def test_can_generate_straight_pipeline(self) -> None:
        pipeline = self._generate_straight_pipeline()
        # Make sure the pipeline is valid in D3M's eyes.
        pipeline.check()

    def test_can_run_straight_pipeline(self) -> None:
        pipeline = self._generate_straight_pipeline()
        run_experimenter_from_pipeline(pipeline, "straight")

    def test_can_generate_wide_pipeline(self) -> None:
        pipeline = self._generate_wide_pipeline()
        # Make sure the pipeline is valid in D3M's eyes.
        pipeline.check()

    def test_can_run_wide_pipeline(self) -> None:
        pipeline = self._generate_wide_pipeline()
        run_experimenter_from_pipeline(pipeline, "wide")

    # Private Methods

    def _generate_random_pipeline(self) -> EZPipeline:
        pipeline = self.experiment.generate_pipeline(
            self.preprocessors,
            self.models[self.problem_type],
            depth=4,
            max_width=3,
            max_num_inputs=2,
        )
        return pipeline

    def _generate_straight_pipeline(self) -> EZPipeline:
        pipeline = self.experiment.generate_pipeline(
            self.preprocessors,
            self.models[self.problem_type],
            depth=6,
            max_width=1,
            max_num_inputs=2,
        )
        return pipeline

    def _generate_wide_pipeline(self) -> EZPipeline:
        pipeline = self.experiment.generate_pipeline(
            self.preprocessors,
            self.models[self.problem_type],
            depth=1,
            max_width=12,
            max_num_inputs=3,
        )
        return pipeline
