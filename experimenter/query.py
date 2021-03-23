from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from experimenter.utils import get_problem_path, get_dataset_doc_path, get_pipelines_from_d3m
from d3m.runtime import _get_data_and_scoring_params_from_pipeline_run as _data_score_params


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
        for (problem_id, dataset_id, data_prep, scoring), params_dict in results.items():
            if limit and len(random_seeds) > limit:
                continue
            data_prep_id, data_prep_seed = data_prep
            scoring_id, scoring_seed = scoring
            random_seeds = params_dict['random_seeds']
            data_params = params_dict['data_params']
            scoring_params = params_dict['scoring_params']
            data_prep_pipeline = get_pipeline(data_prep_id, types='Data')
            scoring_pipeline = get_pipeline(scoring_id, types='Scoring')
            yield {'pipeline': pipeline.to_dict(), 'problem_path': get_problem_path(problem_id), 
                   'dataset_doc_path':get_dataset_doc_path(dataset_id), 'tested_seeds': random_seeds,
                   'data_prep_pipeline': data_prep_pipeline, 'data_prep_seed': data_prep_seed,
                   'scoring_pipeline': scoring_pipeline, 'scoring_seed': scoring_random_seed,
                   'scoring_params': scoring_params, 'data_params': data_params}


def get_pipeline(pipeline_id: str=None, types: str='Data'):
      if (pipeline_id is None):
          return None
      pipeline = get_pipelines_from_d3m(pipeline_id, types=types)
      #get from database if not in d3m module
      if (pipeline is None):
          arguments = {'submitter': None, 'id': data_prep_id}
          search = get_search_query(arguments=arguments)
          pipeline = next(search.scan())
          pipeline = pipeline.to_dict()
      return pipeline


def check_for_data_prep(pipeline_run=None):
    """Only handles cases with an explicit data preparation pipeline
    in the pipeline run
    """
    data_prep = None
    data_prep_id = None
    data_prep_seed = None
    try:
        data_prep = pipeline_run.run.data_preparation
    except:
        data_prep = None
        data_prep_seed = None
    if (data_prep is not None):
        data_prep_seed = data_prep.random_seed
        data_prep_id = data_prep.pipeline.id
        data_prep = data_prep.to_dict()
        data_params = _data_score_params(data_prep.get('steps', []))
        
    return (data_prep_id, data_prep_seed), data_params
    
    
def get_scoring_pipeline(pipeline_run=None):
    scoring = pipeline_run.run.scoring
    scoring_seed = scoring.random_seed
    scoring_id = scoring.pipeline.id
    scoring = scoring.to_dict()
    scoring_params = _data_score_params(scoring.get('steps', [])) 
    return (scoring_id, scoring_seed), scoring_params
     

def get_unique_results(results: dict = None):
    #function for getting unique results from the result dictionary 
    pass


def scan_pipeline_runs(pipeline_id, submitter=None):
    pipeline_run_search = Search(using=CONNECTION, index='pipeline_runs') \
      .query('match', pipeline__id=pipeline_id) \
      .query('match', run__phase='PRODUCE') \
      .query('match', status__state='SUCCESS')
    if submitter:
        pipeline_run_search = pipeline_run_search.query('match', _submitter=submitter)
    results = dict()
    for pipeline_run in pipeline_run_search.scan():
        data_prep, data_params = check_for_data_prep(pipeline_run=pipeline_run)
        scoring, scoring_params = get_scoring_pipeline(pipeline_run)
        for dataset in pipeline_run.datasets:
            dataset_prob_tuple = (pipeline_run.problem.id, dataset.id, data_prep, scoring)
            results[dataset_prob_tuple] = results.get(dataset_prob_tuple, list())
            result_add_dict = {'random_seed': pipeline_run.random_seed, 'data_params': data_params, 'scoring_params': scoring_params}
            results[dataset_prob_tuple].append(results_add_dict) 
    return results
    
