from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from experimenter.utils import get_problem_path, get_dataset_doc_path

HOST = 'https://metalearning.datadrivendiscovery.org/es'
CONNECTION = Elasticsearch(hosts=[HOST], timeout=300)

         
def get_search_query(arguments: dict = None, connection = CONNECTION, index='pipelines'):
    index_search = Search(using=CONNECTION, index=index)
    if arguments['id'] is not None:
        index_search = index_search.query('match', id=arguments['id'])
    if arguments['submitter'] is not None:
        index_search = index_search.query('match', _submitter=arguments['submitter'])
    return index_search


def query_on_seeds(pipeline_id: str=None, limit: int=None, submitter: str='byu'):
    arguments = {'id': pipeline_id, 'submitter': submitter}
    pipeline_search = get_search_query(arguments=arguments, index='pipelines')
    for pipeline in pipeline_search.scan():
        results = scan_pipeline_runs(pipeline.id, submitter)
        for (problem_id, dataset_id, data_prep), random_seeds in results.items():
            if limit and len(random_seeds) > limit:
                continue
            #data_prep_pipeline, data_prep_seed = data_prep
            input_run = data_prep[0]
            yield {'pipeline': pipeline.to_dict(), 'problem_path': get_problem_path(problem_id), 
                   'dataset_doc_path':get_dataset_doc_path(dataset_id), 'tested_seeds': random_seeds,
                   'data_prep_pipeline': data_prep_pipeline, 'data_prep_seed': data_prep_seed}


def get_data_preparation_pipeline(data_pred_id: str=None):
      arguments = {'submitter': None, 'id': data_prep_id}
      data_prep_search = get_search_query(arguments=arguments)
      data_prep_pipeline = next(data_prep_search.scan())
      return data_prep_pipeline


def check_for_data_prep(pipeline_run=None):
    """Only handles cases with an explicit data preparation pipeline
    in the pipeline run
    """
    data_prep = None
    data_prep_pipeline = None
    data_prep_seed = None
    try:
        data_prep = pipeline_run.run.data_preparation
    except:
        data_prep = None
        data_prep_seed = None
    if (data_prep is not None):
        data_prep_seed = data_prep.random_seed
        data_prep_pipeline = get_data_preparation_pipeline(data_prep.pipeline.id)
    return data_prep_pipeline, data_prep_seed


def scan_pipeline_runs(pipeline_id, submitter=None):
    pipeline_run_search = Search(using=CONNECTION, index='pipeline_runs') \
      .query('match', pipeline__id=pipeline_id) \
      .query('match', run__phase='PRODUCE') \
      .query('match', status__state='SUCCESS')
    if submitter:
        pipeline_run_search = pipeline_run_search.query('match', _submitter=submitter)
        results = dict()
    for pipeline_run in pipeline_run_search.scan():
        data_prep_pipeline, data_prep_seed = check_for_data_prep(pipeline_run=pipeline_run)
        for dataset in pipeline_run.datasets:
            dataset_prob_tuple = (pipeline_run.problem.id, dataset.id, (data_prep_pipeline, data_prep_seed))
            results[dataset_prob_tuple] = results.get(dataset_prob_tuple, set())
            results[dataset_prob_tuple].add(pipeline_run.random_seed)
    return results
    
