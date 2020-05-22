import random as rnd
import os
import logging

from d3m import index as d3m_index  # noqa: F401

from byudml.imputer.random_sampling_imputer import RandomSamplingImputer

logger = logging.getLogger(__name__)


# If SEED is provided as an environment variable, use that as
# the random seed. Otherwise, use a random one.
random_seed = int(os.getenv("SEED", rnd.randint(1, 1000000)))
logger.info(f"Using random seed {random_seed}")
random = rnd.Random(random_seed)

SAVE_TO_D3M = os.getenv("SAVE_TO_D3M") == "True"
D3M_DB_SUBMITTER = os.getenv("D3M_DB_SUBMITTER")
D3M_DB_TOKEN = os.getenv("D3M_DB_TOKEN")

try:
    MONGO_HOST = os.environ["MONGO_HOST"]
    MONGO_PORT = int(os.environ["MONGO_PORT"])
    REDIS_HOST = os.environ["REDIS_HOST"]
    REDIS_PORT = int(os.environ["REDIS_PORT"])
except Exception:
    logger.exception("environment variables not set")

# TODO: remove this once the D3M docker image updates
# with the fixes in the 0.6.8 byudml release.
d3m_index.register_primitive(
    RandomSamplingImputer.metadata.query()["python_path"], RandomSamplingImputer
)
