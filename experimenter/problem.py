import os

from d3m.metadata.problem import Problem as D3MProblem
from d3m.container import Dataset


class ProblemReference:
    def __init__(
        self,
        name: str,
        directory: str,
        problem_type: str,
        datasets_dir: str = "/datasets",
    ) -> None:
        """
        :param name: The name of the directory where this problem's files
            can be found.
        :param directory: The path from the root datasets directory to the parent
            directory of the problem directory identified by `name`.
        :param problem_type: The type of ML problem e.g. "classification" or
            "regression".
        :param datasets_dir: The root datasets directory which contains all the
            problem directories (problem directories may not be direct children
            of this).
        """
        self.name = name
        self.path = os.path.join(datasets_dir, directory, self.name)
        self.problem_type = problem_type

    @property
    def data_splits_path(self) -> str:
        return os.path.join(self.path, f"{self.name}_problem", "dataSplits.csv")

    @property
    def problem_doc_path(self) -> str:
        return os.path.join(self.path, f"{self.name}_problem", "problemDoc.json")

    @property
    def dataset_doc_path(self) -> str:
        return os.path.join(self.path, f"{self.name}_dataset", "datasetDoc.json")

    def to_d3m_problem(self) -> D3MProblem:
        return D3MProblem.load(f"file://{self.problem_doc_path}")

    def to_d3m_dataset(self) -> Dataset:
        return Dataset.load(f"file://{self.dataset_doc_path}")
