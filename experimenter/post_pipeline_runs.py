import requests
import json
from pprint import pprint
import urllib.request
from hidden_constants import username, password

import logging

logger = logging.getLogger(__name__)

import yaml

filepath = "/users/guest/o/orionw/database/pipelines/first.json"


def yaml_as_python(val):
    """Convert YAML to dict"""
    try:
        return yaml.load_all(val)
    except yaml.YAMLError as exc:
        return exc


value_list = []
with open(filepath) as input_file:
    results = yaml_as_python(input_file)
    for value in results:
        value_list.append(value)

results = value_list[0]

headers = {"Accept": "application/json", "Content-Type": "application/json"}
url = "https://metalearning.datadrivendiscovery.org/1.0/pipeline/"

payload = json.dumps(results)
plogger.info(payload)
logger.info(len(str(payload)))

r = requests.post(url, data=payload, auth=(username, password), headers=headers)

logger.info(r.status_code)
logger.info(r.text)
