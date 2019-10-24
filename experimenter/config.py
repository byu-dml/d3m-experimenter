import random
import os

from d3m import index as d3m_index
from byudml.imputer.random_sampling_imputer import RandomSamplingImputer

# If SEED is provided as an environment variable, use that as
# the random seed. Otherwise, use a random one.
random_seed = os.getenv('SEED', random.randint(1, 1000000))
random.seed(random_seed)
print("Using random seed", random_seed)

# TODO: Once the `fix-imputer` branch of our d3m-primitives repo
# has been merged and the package re-released to pypi and the new
# pypi version is on the d3m docker image, we can just import
# d3m.index directly and not need to use this modified one.
d3m_index.register_primitive(
    RandomSamplingImputer.metadata.query()['python_path'],
    RandomSamplingImputer
)