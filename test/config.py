from typing import NamedTuple

from experimenter.config import random


class ProblemReference(NamedTuple):
    name: str
    path: str
    problem_type: str


TEST_DATASETS_DIR = "/datasets/training_datasets/seed_datasets_archive"

TEST_PROBLEM_REFERENCES = {
    "38_sick": ProblemReference(
        "38_sick", TEST_DATASETS_DIR + "/38_sick", "classification"
    ),
    "1491_one_hundred_plants_margin": ProblemReference(
        "1491_one_hundred_plants_margin",
        TEST_DATASETS_DIR + "/1491_one_hundred_plants_margin",
        "classification",
    ),
    "185_baseball": ProblemReference(
        "185_baseball", TEST_DATASETS_DIR + "/185_baseball", "classification"
    ),
    "196_autoMpg": ProblemReference(
        "196_autoMpg", TEST_DATASETS_DIR + "/196_autoMpg", "regression"
    ),
}

test_problem_reference = random.choice(list(TEST_PROBLEM_REFERENCES.values()))
print(f'Using "{test_problem_reference.name}" problem for tests')
