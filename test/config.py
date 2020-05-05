from typing import NamedTuple

from experimenter.config import random


class ProblemReference(NamedTuple):
    name: str
    path: str
    problem_type: str


TEST_DATASETS_DIR = "/datasets/seed_datasets_current"

TEST_PROBLEM_REFERENCES = {
    "38_sick_MIN_METADATA": ProblemReference(
        "38_sick_MIN_METADATA",
        TEST_DATASETS_DIR + "/38_sick_MIN_METADATA",
        "classification",
    ),
    "1491_one_hundred_plants_margin_MIN_METADATA": ProblemReference(
        "1491_one_hundred_plants_margin_MIN_METADATA",
        TEST_DATASETS_DIR + "/1491_one_hundred_plants_margin_MIN_METADATA",
        "classification",
    ),
    "185_baseball_MIN_METADATA": ProblemReference(
        "185_baseball_MIN_METADATA",
        TEST_DATASETS_DIR + "/185_baseball_MIN_METADATA",
        "classification",
    ),
    "196_autoMpg_MIN_METADATA": ProblemReference(
        "196_autoMpg_MIN_METADATA",
        TEST_DATASETS_DIR + "/196_autoMpg_MIN_METADATA",
        "regression",
    ),
}

test_problem_reference = random.choice(list(TEST_PROBLEM_REFERENCES.values()))
print(f'Using "{test_problem_reference.name}" problem for tests')
