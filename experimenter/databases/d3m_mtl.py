import logging
import os

import requests
from d3m.primitive_interfaces.base import PrimitiveBase
from d3m.metadata.pipeline import PrimitiveStep, Pipeline

from experimenter.constants import D3M_MTL_DB_URL
from experimenter.problem import ProblemReference

logger = logging.getLogger(__name__)


class D3MMtLDB:
    """
    A class for interfacing with the D3M Metalearning (MtL) database.
    """

    def __init__(self) -> None:
        self._url = D3M_MTL_DB_URL
        # Our submitter name.
        self._submitter = os.getenv("D3M_DB_SUBMITTER")
        # The secret verifying us as the submitter we say we are.
        self._x_token = os.getenv("D3M_DB_TOKEN")
        if self._is_identifying_as_submitter():
            logger.info(
                f"Documents will be saved under submitter name: '{self._submitter}'"
            )

    def save_problem(self, problem: ProblemReference) -> requests.Response:
        d3m_problem = problem.to_d3m_problem()
        # Normalize the problem's form.
        d3m_problem_dict = d3m_problem.to_json_structure(canonical=True)
        return self._save(d3m_problem_dict, "problem")

    def save_dataset(self, problem: ProblemReference) -> requests.Response:
        dataset = problem.to_d3m_dataset()
        # Normalize the dataset's form.
        dataset_dict = dataset.to_json_structure(canonical=True)
        return self._save(dataset_dict, "dataset")

    def save_pipeline(
        self, pipeline: Pipeline, save_primitives: bool = False
    ) -> requests.Response:
        if save_primitives:
            primitives = [
                step.primitive
                for step in pipeline.steps
                if isinstance(step, PrimitiveStep)
            ]
            for primitive in primitives:
                save_successful = self.save_primitive(primitive)
                if not save_successful:
                    return False

        # First, normalize the pipeline's form.
        pipeline_dict = pipeline.to_json_structure(canonical=True)
        return self._save(pipeline_dict, "pipeline")

    def save_primitive(self, primitive: PrimitiveBase) -> requests.Response:
        primitive_dict = primitive.metadata.to_json_structure()
        return self._save(primitive_dict, "primitive")

    def save_pipeline_run(self, pipeline_run: dict) -> requests.Response:
        return self._save(pipeline_run, "pipeline-run")

    def _save(self, entity: dict, index_name: str) -> requests.Response:
        """
        Attempts to save `entity` to the D3M MtL elasticsearch index identified
        by `index_name`. Returns `True` if save was successful, `False` otherwise.
        """
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        params = {}

        if self._is_identifying_as_submitter():
            # We have a D3M credential, so associate that
            # with this entity.
            params["submitter"] = self._submitter
            headers["x-token"] = self._x_token

        response = requests.post(
            f"{self._url}{index_name}/", json=entity, headers=headers, params=params
        )
        if not response.ok:
            logger.error(f"could not save entity {entity} to the {index_name} index")
            logger.error(response.json())
        return response

    def _is_identifying_as_submitter(self) -> bool:
        """
        Returns True if this DB client is posing as a trusted submitter. Note that
        documents can still be saved to the DB without being an trusted submitter.
        """
        return self._submitter is not None and self._x_token is not None
