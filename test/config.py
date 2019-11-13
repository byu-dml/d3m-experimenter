from typing import NamedTuple

from experimenter.config import random

class ProblemReference(NamedTuple):
    name: str
    path: str
    problem_type: str

TEST_PROBLEM_REFERENCES = [
    ProblemReference('sick', '/datasets/seed_datasets_current/38_sick', 'classification'),
    ProblemReference(
        'one_hundred_plants_margin',
        '/datasets/seed_datasets_current/1491_one_hundred_plants_margin',
        'classification'
    ),
    ProblemReference('baseball', '/datasets/seed_datasets_current/185_baseball', 'classification'),
    ProblemReference('autoMpg', '/datasets/seed_datasets_current/196_autoMpg', 'regression')
]

test_problem_reference = random.choice(TEST_PROBLEM_REFERENCES)
print(f'Using "{test_problem_reference.name}" problem for tests')
