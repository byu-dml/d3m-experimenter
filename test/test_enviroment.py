import logging
import unittest

import redis

from experimenter.databases.aml_mtl import PipelineDB
from experimenter.databases.d3m_mtl import D3MMtLDB
from experimenter.config import REDIS_HOST, REDIS_PORT

logger = logging.getLogger(__name__)


class TestEnviroment(unittest.TestCase):
    def test_aml_database(self):
        db = PipelineDB()
        db.get_database_stats()

    def test_d3m_database(self):
        db = D3MMtLDB()
        n = db.search(index="pipelines").count()
        self.assertGreater(n, 0)

    def test_redis(self):
        try:
            conn = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
            conn.ping()
        except Exception as ex:
            print("Error:", ex)
            exit("Failed to connect, terminating.")
