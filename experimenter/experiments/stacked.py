from typing import Dict, List

from d3m.metadata.pipeline import Pipeline

from experimenter.experiments.experiment import Experiment


class StackedArchitectureExperimenter(Experiment):
    """
    Generates diverse pipelines of stacked architectures.
    """

    def generate_pipelines(self, **unused_args) -> Dict[str, List[Pipeline]]:
        """
        TODO: Implement.
        """
        raise NotImplementedError

    def generate_pipeline(self) -> Pipeline:
        """
        TODO: Implement.
        """
        raise NotImplementedError
