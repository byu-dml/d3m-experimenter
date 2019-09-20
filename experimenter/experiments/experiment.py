from abc import ABC, abstractmethod
from typing import Dict, List

from d3m.metadata.pipeline import Pipeline

class Experiment(ABC):
    """
    All experiments that are run by the `experimenter.experimenter`
    module should inherit and implement this abstract class, so they
    match the module's API.
    """

    @abstractmethod
    def generate_pipelines(self) -> Dict[str, List[Pipeline]]:
        """
        Should return a mapping of problem type to a list of
        pipelines outfitted for that problem type e.g.
        `{"classification": [Pipeline()], "regression": [Pipeline()]}`.
        Subclasses can define whatever input parameters they want.
        """
        pass
    
    @abstractmethod
    def generate_pipeline(self) -> Pipeline:
        """
        Should generate a single pipeline
        Subclasses can define whatever input parameters they want.
        """
        pass
