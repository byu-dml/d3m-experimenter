import random
import os

from d3m import index as d3m_index

# If SEED is provided as an environment variable, use that as
# the random seed. Otherwise, use a random one.
random_seed = os.getenv("SEED", random.randint(1, 1000000))
random.seed(random_seed)
print("Using random seed", random_seed)
