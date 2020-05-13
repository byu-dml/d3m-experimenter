import unittest

from experimenter.experiments.straight import StraightArchitectureExperimenter
from experimenter.constants import models, bulletproof_preprocessors
from test.config import test_problem_reference, random
from test.utils import run_experimenter_from_pipeline


class TestStraightPipelines(unittest.TestCase):

    # Test Methods

    def setUp(self):
        self.volumes_dir = "/volumes"
        self.experiment = StraightArchitectureExperimenter()
        self.preprocessors = bulletproof_preprocessors
        self.model_list = models[test_problem_reference.problem_type]

    def test_can_generate_pipeline(self) -> None:
        pipeline = self.experiment.generate_pipeline(
            random.choice(self.preprocessors), random.choice(self.model_list)
        )
        # Make sure the pipeline is valid in D3M's eyes.
        pipeline.check()

    def test_can_run_pipeline(self) -> None:
        pipeline = self.experiment.generate_pipeline(
            random.choice(self.preprocessors), random.choice(self.model_list)
        )
        run_experimenter_from_pipeline(pipeline, "straight")
