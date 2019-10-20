import unittest

from experimenter.experiments.random import RandomArchitectureExperimenter
from experimenter.constants import models, bulletproof_preprocessors, TEST_DATASET_PATHS
from experimenter.pipeline_builder import EZPipeline
from experimenter.run_pipeline import RunPipeline


class TestRandomPipelines(unittest.TestCase):

    # Test Methods

    def setUp(self):
        self.datasets_dir = "/datasets"
        self.volumes_dir = "/volumes"
        self.problem_path = TEST_DATASET_PATHS['38_sick']
        self.experiment = RandomArchitectureExperimenter()
        self.preprocessors = bulletproof_preprocessors
        self.models = models
    
    def test_can_generate_pipeline(self) -> None:
        pipeline = self._generate_random_pipeline()
        # Make sure the pipeline is valid in D3M's eyes.
        pipeline.check()
    
    def test_can_run_pipeline(self) -> None:
        pipeline = self._generate_random_pipeline()
        self._run_experimenter_from_pipeline(pipeline, "wide+deep")
    
    def test_can_generate_straight_pipeline(self) -> None:
        pipeline = self._generate_straight_pipeline()
        # Make sure the pipeline is valid in D3M's eyes.
        pipeline.check()
    
    def test_can_run_straight_pipeline(self) -> None:
        pipeline = self._generate_straight_pipeline()
        self._run_experimenter_from_pipeline(pipeline, "straight")
    
    def test_can_generate_wide_pipeline(self) -> None:
        pipeline = self._generate_wide_pipeline()
        # Make sure the pipeline is valid in D3M's eyes.
        pipeline.check()
    
    def test_can_run_wide_pipeline(self) -> None:
        pipeline = self._generate_wide_pipeline()
        self._run_experimenter_from_pipeline(pipeline, "wide")
    
    # Private Methods

    def _generate_random_pipeline(self) -> EZPipeline:
        pipeline = self.experiment.generate_pipeline(
            self.preprocessors,
            self.models['classification'],
            depth=4,
            max_width=3,
            max_num_inputs=2
        )
        return pipeline

    def _generate_straight_pipeline(self) -> EZPipeline:
        pipeline = self.experiment.generate_pipeline(
            self.preprocessors,
            self.models['classification'],
            depth=6,
            max_width=1,
            max_num_inputs=2
        )
        return pipeline

    def _generate_wide_pipeline(self) -> EZPipeline:
        pipeline = self.experiment.generate_pipeline(
            self.preprocessors,
            self.models['classification'],
            depth=1,
            max_width=12,
            max_num_inputs=3
        )
        return pipeline

    def _run_experimenter_from_pipeline(self, pipeline_to_run: EZPipeline, arch_type: str):
        # run our system
        run_pipeline = RunPipeline(
            datasets_dir=self.datasets_dir,
            volumes_dir=self.volumes_dir,
            problem_path=self.problem_path
        )
        scores_test, _ = run_pipeline.run(pipeline=pipeline_to_run)
        # the value of score is in the first document in the first index
        score = scores_test[0]["value"][0]
        print(f'score for {arch_type} random pipeline: {score}')
        return score
