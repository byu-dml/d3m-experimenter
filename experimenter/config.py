import random as rnd
import os
from d3m import index as d3m_index  # noqa: F401

# If SEED is provided as an environment variable, use that as
# the random seed. Otherwise, use a random one.
random_seed = int(os.getenv("SEED", rnd.randint(1, 1000000)))
print("Using random seed", random_seed)
random = rnd.Random(random_seed)
