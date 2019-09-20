from typing import Dict, List

from d3m.metadata.pipeline import Pipeline

from experimenter.experiments.experiment import Experiment

class RandomArchitectureExperimenter(Experiment):
    """
    Generates diverse pipelines of random architectures.
    """

    def generate_pipelines(self) -> Dict[str, List[Pipeline]]:
        """
        TODO: Implement.
        """
        raise NotImplementedError
    
    def generate_pipeline(self) -> Pipeline:
        """
        TODO: Implement.
        """
        raise NotImplementedError
