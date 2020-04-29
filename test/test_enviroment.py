import pymongo
import redis
import os
import logging
import unittest
from experimenter.database_communication import PipelineDB

logger = logging.getLogger(__name__)

try:
    mongo_host = os.environ['MONGO_HOST']
    mongo_port = int(os.environ['MONGO_PORT'])
    docker_hostname = os.environ['DOCKER_HOSTNAME']
    redis_host = os.environ['REDIS_HOST']
    redis_port = int(os.environ['REDIS_PORT'])
except Exception as E:
    logger.info("ERROR: environment variables not set")
    raise E


class TestEnviroment(unittest.TestCase):

    def test_database(self):
        db = PipelineDB(mongo_host, mongo_port)
        db.get_database_stats()

    def test_redis(self):
        try:
            conn = redis.StrictRedis(
                host=redis_host,
                port=redis_port)
            conn.ping()
        except Exception as ex:
            print('Error:', ex)
            exit('Failed to connect, terminating.')
