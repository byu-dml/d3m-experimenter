import os

from experimenter.config import random
from experimenter.problem import ProblemReference


TEST_DATASETS_ROOT = "./datasets"
TEST_MIN_METADATA_DATASETS_DIR = "seed_datasets_current"
TEST_DATASETS_DIR = "training_datasets/seed_datasets_archive"

TEST_PROBLEM_REFERENCES = {
    # MIN_METADATA problems (ones without metadata)
    "38_sick_MIN_METADATA": ProblemReference(
        "38_sick_MIN_METADATA", TEST_MIN_METADATA_DATASETS_DIR, TEST_DATASETS_ROOT
    ),
    "1491_one_hundred_plants_margin_MIN_METADATA": ProblemReference(
        "1491_one_hundred_plants_margin_MIN_METADATA",
        TEST_MIN_METADATA_DATASETS_DIR,
        TEST_DATASETS_ROOT,
    ),
    "185_baseball_MIN_METADATA": ProblemReference(
        "185_baseball_MIN_METADATA", TEST_MIN_METADATA_DATASETS_DIR, TEST_DATASETS_ROOT
    ),
    "196_autoMpg_MIN_METADATA": ProblemReference(
        "196_autoMpg_MIN_METADATA", TEST_MIN_METADATA_DATASETS_DIR, TEST_DATASETS_ROOT
    ),
    # Problems with metadata
    "38_sick": ProblemReference("38_sick", TEST_DATASETS_DIR, TEST_DATASETS_ROOT),
    "1491_one_hundred_plants_margin": ProblemReference(
        "1491_one_hundred_plants_margin", TEST_DATASETS_DIR, TEST_DATASETS_ROOT,
    ),
    "185_baseball": ProblemReference(
        "185_baseball", TEST_DATASETS_DIR, TEST_DATASETS_ROOT
    ),
    "196_autoMpg": ProblemReference(
        "196_autoMpg", TEST_DATASETS_DIR, TEST_DATASETS_ROOT
    ),
}

_test_problem_name = os.getenv(
    "PROBLEM", random.choice(list(TEST_PROBLEM_REFERENCES.keys()))
)
test_problem_reference = TEST_PROBLEM_REFERENCES[_test_problem_name]
print(f'Using "{test_problem_reference.name}" problem for tests')
