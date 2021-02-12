import configparser
import logging
import os.path


logger = logging.getLogger(__name__)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    def __init__(self, config_path: str = None) -> None:
        if config_path is None:
            config_path = './config.ini'

        if not os.path.isfile(config_path):
            msg = 'config file not found at {}'.format(config_path)
            logger.error(msg)
            raise exceptions.ConfigurationError(msg)

        self._config_path = config_path
        self._config = configparser.ConfigParser()
        self._config.read(config_path)

    def get(self, section, key):
        return self._config.get(section, key)


class RedisConfig(metaclass=Singleton):
    def __init__(self):
        config = Config()
        self.host = config.get('REDIS', 'HOST')
        self.port = int(config.get('REDIS', 'PORT'))
        self.data_dir = os.path.abspath(os.path.join(
            config.get('MAIN', 'CACHE_DIR'), config.get('REDIS', 'DATA_DIR')
        ))
        self.docker_image_name = config.get('REDIS', 'DOCKER_IMAGE_NAME')
        self.docker_port = int(config.get('REDIS', 'DOCKER_PORT'))
        self.docker_data_dir = config.get('REDIS', 'DOCKER_DATA_DIR')
        self.dashboard_port = config.get('REDIS', 'DASHBOARD_PORT')
        self.dashboard_docker_image_name = config.get('REDIS', 'DASHBOARD_DOCKER_IMAGE_NAME')
