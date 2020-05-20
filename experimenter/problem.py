import os
import json
import logging

from d3m.metadata.problem import Problem as D3MProblem
from d3m.container import Dataset

logger = logging.getLogger(__name__)


class ProblemReference:
    def __init__(self, name: str, directory: str, datasets_dir: str) -> None:
        """
        :param name: The name of the directory where this problem's files
            can be found.
        :param directory: The path from the root datasets directory to the parent
            directory of the problem directory identified by `name`.
        :param datasets_dir: The root datasets directory which contains all the
            problem directories (problem directories may not be direct children
            of this).
        """
        # The name of the problem/dataset. Also the same as the root directory
        # the problem lives in.
        self.name = name
        # The path to the root directory of the problem and dataset.
        self.path = os.path.join(datasets_dir, directory, self.name)
        self._load_and_set_attributes()

    @property
    def data_splits_path(self) -> str:
        return os.path.join(self.path, f"{self.name}_problem", "dataSplits.csv")

    @property
    def problem_doc_path(self) -> str:
        return os.path.join(self.path, f"{self.name}_problem", "problemDoc.json")

    @property
    def dataset_doc_path(self) -> str:
        return os.path.join(self.path, f"{self.name}_dataset", "datasetDoc.json")

    def get_dataset_id(self) -> str:
        return json.load(open(self.dataset_doc_path))["about"]["datasetID"]

    def to_d3m_problem(self) -> D3MProblem:
        return D3MProblem.load(f"file://{self.problem_doc_path}")

    def to_d3m_dataset(self) -> Dataset:
        return Dataset.load(f"file://{self.dataset_doc_path}")

    def _load_and_set_attributes(self):
        """
        Gathers various attributes about the problem and its dataset
        using its problem document and dataset document.
        """
        # Gather data about the problem.
        with open(self.problem_doc_path, "r") as f:
            problem_doc = json.load(f)

        self.task_keywords = problem_doc["about"]["taskKeywords"]
        if "classification" in self.task_keywords:
            self.problem_type = "classification"
        elif "regression" in self.task_keywords:
            self.problem_type = "regression"
        else:
            self.problem_type = None

        self.problem_id = problem_doc["about"]["problemID"]

        # Gather data about the problem's dataset.
        with open(self.dataset_doc_path, "r") as f:
            dataset_doc = json.load(f)

        self.dataset_id = dataset_doc["about"]["datasetID"]
        self.dataset_digest = dataset_doc["about"]["digest"]
