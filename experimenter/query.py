from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from experimenter.utils import get_problem_path, get_dataset_doc_path, get_pipelines_from_d3m
from d3m.runtime import _get_data_and_scoring_params_from_pipeline_run as _data_score_params
from experimenter import config, exceptions

CONNECTION = Elasticsearch(hosts=[config.query_host], timeout=config.query_timeout)

         
def match_query(index:str, arguments: dict = None, connection = CONNECTION):
    #remove None arguments from the dictionary
    filtered_args = {k:v for k,v in arguments.items() if v is not None}
    #initialize the search
    index_search = Search(using=connection, index=index)
    for field, argument in filtered_args.items():
        arg_dict = dict()
        arg_dict[field] = argument
        index_search = index_search.query('match', **arg_dict)
    return index_search


def unpack_run_tuple_args(run_tuple: tuple):
    #unpack values from tuple
    problem_id, dataset_id, data_prep_data, scoring_data = run_tuple
    scoring_id, scoring_random_seed = scoring_data
    data_prep_id, data_prep_seed = data_prep_data
    #get preparation and scoring pipelines
    data_prep_pipeline = get_pipeline(data_prep_id, types='Data')
    scoring_pipeline = get_pipeline(scoring_id, types='Scoring')
    return {'problem_path': get_problem_path(problem_id), 
           'dataset_doc_path':get_dataset_doc_path(dataset_id),
           'data_prep_pipeline': data_prep_pipeline, 'data_prep_seed': data_prep_seed,
           'scoring_pipeline': scoring_pipeline, 'scoring_seed': scoring_random_seed,}


def get_pipeline(pipeline_id: str=None, types: str='Data'):
      """
      gets a pipeline from the database, if it is not already
      in the d3m module
      """
      if (pipeline_id is None):
          return None
      pipeline = get_pipelines_from_d3m(pipeline_id, types=types)
      #get from database if not in d3m module
      if (pipeline is None):
          arguments = {'id': data_prep_id}
          search = match_query(index='pipelines', arguments=arguments)
          pipeline = next(search.scan())
          pipeline = pipeline.to_dict()
      return pipeline


def check_for_data_prep(pipeline_run=None):
    """Handles cases with an explicit data preparation pipeline
    in the pipeline run, will return none when pipeline run has
    no preparation pipeline
    """
    try:
        data_prep = pipeline_run.run.data_preparation
        data_prep_seed = data_prep.random_seed
        data_prep_id = data_prep.pipeline.id
        data_prep = data_prep.to_dict()
        data_params = _data_score_params(data_prep.get('steps', []))
    except KeyError:
        #no data preparation pipeline in pipeline run, return none
        data_prep, data_prep_seed, data_prep_id, data_params = None
        
    return (data_prep_id, data_prep_seed), data_params
    
    
def get_scoring_pipeline(pipeline_run):
    """
    returns the scoring pipeline from the pipeline run
    """
    scoring = pipeline_run.run.scoring
    scoring_seed = scoring.random_seed
    scoring_id = scoring.pipeline.id
    scoring = scoring.to_dict()
    scoring_params = _data_score_params(scoring.get('steps', [])) 
    return (scoring_id, scoring_seed), scoring_params
     

def get_list_duplicates(params_list, match_item):
    """
    takes in a list of params and an item to match,
    returns a list of matching indeces in the list
    """
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


def combine_unique_params(param_dict_list: dict = None):
    """
    reduces the param_dict_list into a list of unique paramers with
    combined random seeds
    """
    random_seeds_list = param_dict_list['random_seeds']
    params_list = param_dict_list['params']
    final_list = list()
    location_dict = dict() #initalize dictionary for storing matchine indices
    #loop through the parameter values
    for it, param in enumerate(params_list):
        #get matching pairs of each value 
        location_dict[it] = get_list_duplicates(params_list, param)
    skip = set() #initialize set of locations to skip
    for loc, values in location_dict.items():
        #only need to match once to match in other locations (add to skip)
        if loc in skip:
            continue
        random_seeds = set()
        for value in values:
            #add matched params random seeds to same set
            random_seeds.add(random_seeds_list[value])
            skip.add(value)
        data_params, scoring_params = params_list[loc]
        #combine matching params with aggregated set of random seeds
        final_list.append({'data_params': data_params, 'scoring_params': scoring_params, 'random_seeds': random_seeds})
    return final_list


def scan_pipeline_runs(pipeline_id, submitter=None):
    query_arguments = {'pipeline__id': pipeline_id, 'run__phase': 'PRODUCE', 
                       'status__state': 'SUCCESS', '_submitter': submitter}
    pipeline_run_search = match_query(index='pipeline_runs', arguments=query_arguments)
    query_results = dict()
    for pipeline_run in pipeline_run_search.scan():
        data_prep, data_params = check_for_data_prep(pipeline_run=pipeline_run)
        scoring, scoring_params = get_scoring_pipeline(pipeline_run)
        for dataset in pipeline_run.datasets:
            run_tuple = (pipeline_run.problem.id, dataset.id, data_prep, scoring)
            query_results[run_tuple] = query_results.get(run_tuple, dict())
            query_results[run_tuple]['random_seeds'] = query_results[run_tuple].get('random_seed', list())
            query_results[run_tuple]['params'] = query_results[run_tuple].get('params', list())
            query_results[run_tuple]['random_seeds'].append(pipeline_run.random_seed)
            query_results[run_tuple]['params'].append((data_params, scoring_params))
    return query_results
    
