import os
import json
import logging

from d3m.metadata.problem import Problem as D3MProblem
from d3m.container import Dataset

from experimenter.constants import PROBLEM_BLACKLIST

logger = logging.getLogger(__name__)


class ProblemReference:
    subsets = {"ALL", "TRAIN", "TEST", "SCORE"}

    def __init__(
        self, name: str, directory: str, datasets_dir: str, subset: str = "ALL"
    ) -> None:
        """
        :param name: The name of the directory where this problem's files
            can be found.
        :param directory: The path from the root datasets directory to the parent
            directory of the problem directory identified by `name`.
        :param datasets_dir: The root datasets directory which contains all the
            problem directories (problem directories may not be direct children
            of this).
        :param subset: The subset of this problem/dataset to use.
        """
        # The name of the problem/dataset. Also the same as the root directory
        # the problem lives in.
        self.name = name
        # The path to the root directory of the problem and dataset.
        self.path = os.path.join(datasets_dir, directory, self.name)

        assert subset in self.subsets
        self.subset = subset

        self._load_problem_docs()
        self._load_dataset_docs()

    # Problem-related attributes and methods

    def _load_problem_docs(self) -> None:
        # We'll temporarilly change `self.subset` in order to load
        # all the problem docs.
        user_subset = self.subset

        self._problem_docs = {}
        for subset in self.subsets:
            self.subset = subset
            if os.path.isfile(self.problem_doc_path):
                self._problem_docs[self.subset] = json.load(open(self.problem_doc_path))

        self.subset = user_subset

    @property
    def problem_dir(self) -> str:
        if self.subset == "ALL":
            return os.path.join(self.path, f"{self.name}_problem")
        elif self.subset in self.subsets:
            return os.path.join(self.path, self.subset, f"problem_{self.subset}")
        else:
            raise ValueError(
                f"Unsupported value for self.subset '{self.subset}'. "
                f"Valid options are {self.subsets}"
            )

    @property
    def data_splits_path(self) -> str:
        return os.path.join(self.problem_dir, "dataSplits.csv")

    @property
    def problem_doc_path(self) -> str:
        return os.path.join(self.problem_dir, "problemDoc.json")

    @property
    def problem_doc(self) -> dict:
        if self.subset not in self._problem_docs:
            # This problem has no problem document for the
            # `self.subset` subset.
            return None
        return self._problem_docs[self.subset]

    @property
    def task_keywords(self) -> list:
        return self.problem_doc["about"]["taskKeywords"]

    @property
    def problem_type(self):
        if "classification" in self.task_keywords:
            return "classification"
        elif "regression" in self.task_keywords:
            return "regression"
        else:
            return None

    def to_d3m_problem(self) -> D3MProblem:
        return D3MProblem.load(f"file://{self.problem_doc_path}")

    # Dataset-related attributes and methods

    def _load_dataset_docs(self) -> None:
        # We'll temporarilly change `self.subset` in order to load
        # all the dataset docs.
        user_subset = self.subset

        self._dataset_docs = {}
        for subset in self.subsets:
            self.subset = subset
            if os.path.isfile(self.dataset_doc_path):
                self._dataset_docs[self.subset] = json.load(open(self.dataset_doc_path))

        self.subset = user_subset

    @property
    def dataset_dir(self) -> str:
        if self.subset == "ALL":
            return os.path.join(self.path, f"{self.name}_dataset")
        elif self.subset in self.subsets:
            return os.path.join(self.path, self.subset, f"dataset_{self.subset}")
        else:
            raise ValueError(
                f"Unsupported value for self.subset '{self.subset}'. "
                f"Valid options are {self.subsets}"
            )

    @property
    def dataset_doc_path(self) -> str:
        return os.path.join(self.dataset_dir, "datasetDoc.json")

    @property
    def dataset_doc(self) -> dict:
        if self.subset not in self._dataset_docs:
            # This problem has no dataset document for the
            # `self.subset` subset.
            return None
        return self._dataset_docs[self.subset]

    @property
    def dataset_id(self) -> str:
        return self.dataset_doc["about"]["datasetID"]

    @property
    def dataset_digest(self) -> str:
        return self.dataset_doc["about"]["digest"]

    def to_d3m_dataset(self) -> Dataset:
        return Dataset.load(f"file://{self.dataset_doc_path}")

    # Other attributes and methods

    @property
    def is_blacklisted(self) -> bool:
        """
        `True` if this problem is blacklisted i.e. if we don't want
        to run any pipelines on it because its too big or of the wrong format.
        """
        normalized_name = self.name.replace("_MIN_METADATA", "")
        return normalized_name in PROBLEM_BLACKLIST
