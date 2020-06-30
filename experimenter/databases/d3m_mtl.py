import logging
import json

import requests
from d3m.primitive_interfaces.base import PrimitiveBase
from d3m.metadata.pipeline import PrimitiveStep, Pipeline
from elasticsearch_dsl import Search
from elasticsearch import Elasticsearch

from experimenter.constants import D3M_MTL_DB_POST_URL, D3M_MTL_DB_GET_URL
from experimenter.problem import ProblemReference
from experimenter import config

logger = logging.getLogger(__name__)


class D3MMtLDB:
    """
    A class for interfacing with the D3M Metalearning (MtL) database.
    """

    def __init__(self) -> None:
        self._post_url = D3M_MTL_DB_POST_URL
        # This env var allows code calling this class to be run during
        # unit tests without actually saving to the production DB.
        self.should_save = config.SAVE_TO_D3M
        # A reference to a low-level elasticsearch client. This can be
        # used to query the D3M DB, or this classe's `search` method
        # can be used, and is preferred, since its API is more straightforward.
        # This low-level client is the only way to accomplish
        # certain things though.
        self.es = Elasticsearch(hosts=[D3M_MTL_DB_GET_URL], timeout=30)
        # Our submitter name.
        self._submitter = config.D3M_DB_SUBMITTER
        # The secret verifying us as the submitter we say we are.
        self._x_token = config.D3M_DB_TOKEN
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
                primitive_save_result = self.save_primitive(primitive)
                if not primitive_save_result.ok:
                    return primitive_save_result

        # First, normalize the pipeline's form.
        pipeline_dict = pipeline.to_json_structure(canonical=True)
        return self._save(pipeline_dict, "pipeline")

    def save_primitive(self, primitive: PrimitiveBase) -> requests.Response:
        primitive_dict = primitive.metadata.to_json_structure()
        return self._save(primitive_dict, "primitive")

    def search(self, *args, **kwargs) -> Search:
        """
        Wraps a call to `elasticsearch_dsl.Search` so it doesn't have to imported
        along with this class. The main argument to pass to search is
        `index` e.g. `index="pipelines"`. See the documentation:
        https://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html
        """
        return Search(using=self.es, *args, **kwargs)

    def has_pipeline_been_run_on_problem(
        self, pipeline: Pipeline, problem: ProblemReference
    ) -> bool:
        num_pipeline_dataset_matches = (
            self.search(index="pipeline_runs")
            .query("match", pipeline__digest=pipeline.get_digest())
            .query("match", datasets__id=problem.dataset_id)
            .query("match", datasets__digest=problem.dataset_digest)
            .count()
        )
        return num_pipeline_dataset_matches > 0

    def save_pipeline_run(self, pipeline_run: dict) -> requests.Response:
        return self._save(pipeline_run, "pipeline-run")

    def _save(self, entity: dict, index_name: str) -> requests.Response:
        """
        Attempts to save `entity` to the D3M MtL elasticsearch index identified
        by `index_name`. Returns `True` if save was successful, `False` otherwise.
        """
        if not self.should_save:
            return self._create_no_save_response()

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        params = {}

        if self._is_identifying_as_submitter():
            # We have a D3M credential, so associate that
            # with this entity.
            params["submitter"] = self._submitter
            headers["x-token"] = self._x_token

        response = requests.post(
            f"{self._post_url}/{index_name}/",
            json=entity,
            headers=headers,
            params=params,
        )
        if not response.ok:
            logger.error(
                f"could not save entity {self._get_partial_json(entity)} "
                f"to the {index_name} index (HTTP code {response.status_code})"
            )
            logger.error(response.json())
        return response

    def _is_identifying_as_submitter(self) -> bool:
        """
        Returns True if this DB client is posing as a trusted submitter. Note that
        documents can still be saved to the DB without being an trusted submitter.
        """
        return self._submitter is not None and self._x_token is not None

    def _create_no_save_response(self) -> requests.Response:
        """
        This is a dummy response we send when the experimenter is not configured to
        save to the D3M database.
        """
        response = requests.Response()
        response.status_code = 200
        response._content = (
            b'{ "result" : "No request was made to the D3M DB API to save a record, '
            b'since the SAVE_TO_D3M environment variable is not set." }'
        )
        return response

    def _get_partial_json(self, data, length: int = 200) -> str:
        """
        Returns a string representation of `data`, truncated to
        the first `length` characters. Useful for printing.
        """
        return json.dumps(data)[:length] + "..."
