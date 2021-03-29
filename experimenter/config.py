import logging
import os

from experimenter import exceptions


logger = logging.getLogger(__name__)


_ERROR_MESSAGE = 'environment variable not set: {}'


#parse the .env file
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


query_host: str = os.environ.get('QUERY_HOST', 'https://metalearning.datadrivendiscovery.org/es')
def validate_query_host():
    if query_host is None:
        raise exceptions.ConfigError(_ERROR_MESSAGE.format('QUERY_HOST'))
        
        
query_timeout: int = int(os.environ.get('QUERY_TIMEOUT', '500'))
def validate_query_timeout():
    if query_timeout is None:
        raise exceptions.ConfigError(_ERROR_MESSAGE.format('QUERY_TIMEOUT'))


#get the save paths for the experimenter from the point of view of the docker container
output_run_path: str = os.path.abspath(os.path.join('/data', 'pipeline_runs'))
if (not os.path.exists(output_run_path)):
    #create the directory
    os.makedirs(output_run_path, exist_ok=True)
    
    
pipelines_path: str = os.path.abspath(os.path.join('/data', 'pipelines'))
if (not os.path.exists(pipelines_path)):
    #create the directory
    os.makedirs(pipelines_path, exist_ok=True)


data_prep_pipelines_path: str = os.path.abspath(os.path.join('/data', 'data-preparation-pipelines'))
if (not os.path.exists(data_prep_pipelines_path)):
    #create the directory
    os.makedirs(data_prep_pipelines_path, exist_ok=True)


scoring_pipelines_path: str = os.path.abspath(os.path.join('/data', 'scoring-pipelines'))
if (not os.path.exists(scoring_pipelines_path)):
    #create the directory
    os.makedirs(scoring_pipelines_path, exist_ok=True)
