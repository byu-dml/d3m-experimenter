import logging
import os

from experimenter import exceptions


logger = logging.getLogger(__name__)


_ERROR_MESSAGE = 'environment variable not set: {}'


datasets_dir: str = os.environ.get('DATASETS_DIR', None)
def validate_datasets_dir():
    if datasets_dir is None:
        raise exceptions.ConfigError(_ERROR_MESSAGE.format('DATASETS_DIR'))


# this should have a reasonable default
data_dir: str = os.environ.get('DATA_DIR', None)
def validate_data_dir():
    if data_dir is None:
        raise exceptions.ConfigError(_ERROR_MESSAGE.format('DATA_DIR'))


redis_host: str = os.environ.get('REDIS_HOST', None)
def validate_redis_host():
    if redis_host is None:
        raise exceptions.ConfigError(_ERROR_MESSAGE.format('REDIS_HOST'))
        

d3m_db_submitter: str = os.environ.get('D3M_DB_SUBMITTER', None)
def validate_d3m_db_submitter():
    if d3m_db_submitter is None:
        raise exceptions.ConfigError(_ERROR_MESSAGE.format('D3M_DB_SUBMITTER'))


d3m_db_token: str = os.environ.get('D3M_DB_TOKEN', None)
def validate_d3m_db_token():
    if d3m_db_token is None:
        raise exceptions.ConfigError(_ERROR_MESSAGE.format('D3M_DB_TOKEN'))
        
     
save_to_d3m: bool = os.environ.get('SAVE_TO_D3M', None) == 'true'
def validate_save():
    if save_to_d3m is None:
        raise exceptions.ConfigError(_ERROR_MESSAGE.format('SAVE_TO_D3M'))

