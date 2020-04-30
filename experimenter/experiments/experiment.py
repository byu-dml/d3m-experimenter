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
    def generate_pipelines(self, **args) -> Dict[str, List[Pipeline]]:
        """
        Should return a mapping of problem type to a list of
        pipelines outfitted for that problem type e.g.
        `{"classification": [Pipeline()], "regression": [Pipeline()]}`.

        Subclasses inheriting this method should always gather up the
        remaining keyword arguments, since all CLI arguments are passed
        to this function when called by the `Experimenter` class. This
        function can choose which CLI arguments to subscribe to by
        adding them as keyword arguments to the function signature.
        """
        pass

    @abstractmethod
    def generate_pipeline(self) -> Pipeline:
        """
        Should generate a single pipeline
        Subclasses can define whatever input parameters they want.
        """
        pass
