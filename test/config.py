from experimenter.config import random

TEST_DATASET_PATHS = {
    'sick': '/datasets/seed_datasets_current/38_sick',
    # TODO: Uncomment once the one hot encoder logic is
    # revamped, so a test can be randomly chosen each time
    # the tests are run.
    # 'one_hundred_plants_margin': '/datasets/seed_datasets_current/1491_one_hundred_plants_margin',
    # 'autoMpg': '/datasets/seed_datasets_current/196_autoMpg',
    # 'baseball': '/datasets/seed_datasets_current/185_baseball'
}

problem_name, = random.sample(TEST_DATASET_PATHS.keys(), 1)
print(f'Using "{problem_name}" problem for tests')
problem_path: str = TEST_DATASET_PATHS[problem_name]