from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from experimenter.utils import get_problem_path, get_dataset_doc_path

HOST = 'https://metalearning.datadrivendiscovery.org/es'
CONNECTION = Elasticsearch(hosts=[HOST], timeout=300)

def query_on_primitive(primitive_id: str, limit_indexes=False):
   '''Queries the metalearning database for pipelines using the specified primitive.
   Queries the metalearning database using the Elasticsearch endpoint documented
   on D3M's website (see https://metalearning.datadrivendiscovery.org for more
   info). Finds all pipelines containing a certain primitive as specified by the
   keyword argument. Also determines the index(es) of that primitive in each
   matching pipeline and gets the datasets that were used in pipeline runs.
   
   Arguments
   ---------
   primitive_id : str
      A primitive's unique id.
   limit_indexes : 'first', 'last', or False (default)
      Limits which index of the primitive is returned for each pipeline match.
      Use 'first' to get the index of the first matching primitive specified by
      the keyword arg. Use 'last' to get the index of the last match. Use False
      (default) to get a list of all indexes for each pipeline specifying where
      the primitive is.
   
   Yields
   -------
   A list of tuples where each tuple contains (in this order):
      1. a matching pipeline
      2. the index(es) of the desired primitives in the given pipeline's steps
      3. a dictionary containing the datasets used in pipeline runs where the key
         is the dataset digest and the value is the dataset id (human-readable string).
      4. the random seeds used in pipeline runs.
   '''

   if limit_indexes not in { 'first', 'last', False }:
      raise ValueError(f'Invalid value "{limit_indexes}" for arg limit_indexes')
   
   match_query = Q('match', steps__primitive__id=primitive_id)
   nested_query = Q('nested', path='steps', query=match_query)
   pipeline_search = Search(using=CONNECTION, index='pipelines').query(nested_query)

   for pipeline in pipeline_search.scan():
      results = scan_pipeline_runs(pipeline.id)

      locs = [i for i, step in enumerate(pipeline.steps) if primitive_id == step.primitive.id]
      if limit_indexes == 'last':
         locs = locs[-1]
      elif limit_indexes == 'first':
         locs = locs[0]
      
      for (problem_id, dataset_name), random_seeds in results.items():
         
         yield {'pipeline': pipeline.id, 'problem_path': get_problem_path(problem_id), 'location': locs, 'dataset_doc_path': get_dataset_doc_path(dataset_id), 'tested_seeds': random_seeds}

def query_on_seeds(pipeline_id: str=None, limit: int=None, submitter: str='byu'):
   pipeline_search = Search(using=CONNECTION, index='pipelines')
   if pipeline_id:
      pipeline_search = pipeline_search.query('match', id=pipeline_id)
   if submitter:
      pipeline_search = pipeline_search.query('match', _submitter=submitter)
   
   for pipeline in pipeline_search.scan():
      results = scan_pipeline_runs(pipeline.id, submitter)
      for (problem_id, dataset_id), random_seeds in results.items():
         if limit and len(random_seeds) > limit:
            continue
         yield {'pipeline': pipeline.to_dict(), 'problem_path': get_problem_path(problem_id[:-8]), 'dataset_doc_path': get_dataset_doc_path(dataset_id[:-13]), 'tested_seeds': random_seeds}

def scan_pipeline_runs(pipeline_id, submitter=None):
   pipeline_run_search = Search(using=CONNECTION, index='pipeline_runs') \
      .query('match', pipeline__id=pipeline_id) \
      .query('match', run__phase='PRODUCE') \
      .query('match', status__state='SUCCESS')
   if submitter:
      pipeline_run_search = pipeline_run_search.query('match', _submitter=submitter)

   results = dict()
   for pipeline_run in pipeline_run_search.scan():
      for dataset in pipeline_run.datasets:
         dataset_prob_tuple = (pipeline_run.problem.id, dataset.id)
         results[dataset_prob_tuple] = results.get(dataset_prob_tuple, set())
         results[dataset_prob_tuple].add(pipeline_run.random_seed)
   return results
