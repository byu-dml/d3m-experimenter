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
        for dataset_prob_tuple, results_dict in results.items():
            unique_items = get_unique_results(results_dict)
            #unpack values from tuple
            problem_id, dataset_id, data_prep, scoring = dataset_prob_tuple
            scoring_id, scoring_random_seed = scoring
            data_prep_id, data_prep_seed = data_prep
            #get preparation and scoring pipelines
            data_prep_pipeline = get_pipeline(data_prep_id, types='Data')
            scoring_pipeline = get_pipeline(scoring_id, types='Scoring')
            for params in unique_items:
                data_params = params['data_params']
                scoring_params = params['scoring_params']
                random_seeds = params['random_seeds']    
                if limit and len(random_seeds) > limit:
                    continue
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
    data_params = None
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
     

def get_list_duplicates(params_list, match_item):
    start_loc = -1
    locs = []
    while True:
        try:
            loc = params_list.index(match_item,start_loc+1)
        except ValueError:
            break
        else:
            locs.append(loc)
            start_loc = loc
    return locs


def get_unique_results(results: dict = None):
    #function for getting unique results from the result dictionary 
    random_seeds_list = results['random_seeds']
    params_list = results['params']
    final_list = list()
    location_dict = dict()
    #loop through the values
    for it, param in enumerate(params_list):
        #get matching pairs of each value 
        location_dict[it] = get_list_duplicates(params_list, param)
    skip = set()
    for loc, values in location_dict.items():
        if loc in skip:
            continue
        random_seeds = set()
        for value in values:
            random_seeds.add(random_seeds_list[value])
            skip.add(value)
        data_params, scoring_params = params_list[loc]
        final_list.append({'data_params': data_params, 'scoring_params': scoring_params, 'random_seeds': random_seeds})
    return final_list


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
            results[dataset_prob_tuple] = results.get(dataset_prob_tuple, dict())
            results[dataset_prob_tuple]['random_seeds'] = results[dataset_prob_tuple].get('random_seed', list())
            results[dataset_prob_tuple]['params'] = results[dataset_prob_tuple].get('params', list())
            results[dataset_prob_tuple]['random_seeds'].append(pipeline_run.random_seed)
            results[dataset_prob_tuple]['params'].append((data_params, scoring_params))
    return results
    
