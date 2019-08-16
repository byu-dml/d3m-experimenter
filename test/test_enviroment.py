import pymongo
import redis
import os
import logging
import unittest
from experimenter.database_communication import PipelineDB

logger = logging.getLogger(__name__)

try:
    real_mongo_port = int(os.environ['REAL_MONGO_PORT'])
    real_mongo_port_dev = int(os.environ['REAL_MONGO_PORT_DEV'])
    default_mongo_port = int(os.environ['DEFAULT_MONGO_PORT'])
    lab_hostname = os.environ['LAB_HOSTNAME']
    docker_hostname = os.environ['DOCKER_HOSTNAME']
    env_mode = os.environ['MODE']
    redis_host = os.environ['REDIS_HOST']
    redis_port = int(os.environ['REDIS_PORT'])
except Exception as E:
    logger.info("ERROR: environment variables not set")
    raise E


class TestEnviroment(unittest.TestCase):

    def test_database(self):
        db = PipelineDB(lab_hostname, real_mongo_port)
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