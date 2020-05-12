import os

from experimenter.config import random


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


TEST_MIN_METADATA_DATASETS_DIR = "seed_datasets_current"
TEST_DATASETS_DIR = "training_datasets/seed_datasets_archive"

TEST_PROBLEM_REFERENCES = {
    # MIN_METADATA problems (ones without metadata)
    "38_sick_MIN_METADATA": ProblemReference(
        "38_sick_MIN_METADATA", TEST_MIN_METADATA_DATASETS_DIR, "classification",
    ),
    "1491_one_hundred_plants_margin_MIN_METADATA": ProblemReference(
        "1491_one_hundred_plants_margin_MIN_METADATA",
        TEST_MIN_METADATA_DATASETS_DIR,
        "classification",
    ),
    "185_baseball_MIN_METADATA": ProblemReference(
        "185_baseball_MIN_METADATA", TEST_MIN_METADATA_DATASETS_DIR, "classification",
    ),
    "196_autoMpg_MIN_METADATA": ProblemReference(
        "196_autoMpg_MIN_METADATA", TEST_MIN_METADATA_DATASETS_DIR, "regression",
    ),
    # Problems with metadata
    "38_sick": ProblemReference("38_sick", TEST_DATASETS_DIR, "classification"),
    "1491_one_hundred_plants_margin": ProblemReference(
        "1491_one_hundred_plants_margin", TEST_DATASETS_DIR, "classification"
    ),
    "185_baseball": ProblemReference(
        "185_baseball", TEST_DATASETS_DIR, "classification"
    ),
    "196_autoMpg": ProblemReference("196_autoMpg", TEST_DATASETS_DIR, "regression"),
}

test_problem_name = os.getenv(
    "PROBLEM", random.choice(list(TEST_PROBLEM_REFERENCES.keys()))
)
test_problem_reference = TEST_PROBLEM_REFERENCES[test_problem_name]
print(f'Using "{test_problem_reference.name}" problem for tests')
