from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from tqdm import tqdm
from experimenter.utils import get_problem_parent_dir, build_problem_reference

HOST = 'https://metalearning.datadrivendiscovery.org/es'
CONNECTION = Elasticsearch(hosts=[HOST], timeout=300)

def pipeline_with_primitive_generator(primitive_id: str, limit_indexes=False):
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
      problem_ids, random_seeds = scan_pipeline_runs(pipeline.id)

      locs = [i for i, step in enumerate(pipeline.steps) if primitive_id == step.primitive.id]
      if limit_indexes == 'last':
         locs = locs[-1]
      elif limit_indexes == 'first':
         locs = locs[0]
      
      for problem_id in problem_ids:
         yield pipeline.to_dict(), build_problem_reference(problem_id), locs, random_seeds

def test_pipeline(pipeline_id: str):
    pipeline_search = Search(using=CONNECTION, index='pipelines')
    pipeline_search = pipeline_search.query('match', id=pipeline_id)
    for pipeline in pipeline_search.scan():
        problem_ids, random_seeds = set(), set()
        pipeline_run_search = Search(using=CONNECTION, index='pipeline_runs') \
        .query('match', pipeline__id=pipeline_id) \
        .query('match', run__phase='PRODUCE') \
        .query('match', status__state='SUCCESS')
        for pipeline_run in pipeline_run_search.scan():
            random_seeds.add(pipeline_run.random_seed)
            problem_ids.add(pipeline_run.problem.id)
    return pipeline.to_dict(), build_problem_reference(problem_ids.pop()), random_seeds

def pipeline_generator(pipeline_id: str=None):
   pipeline_search = Search(using=CONNECTION, index='pipelines')
   if pipeline_id:
      pipeline_search = pipeline_search.query('match', id=pipeline_id)
   for pipeline in pipeline_search.scan():
      problem_ids, random_seeds = scan_pipeline_runs(pipeline.id)
      for problem_id in problem_ids:
         yield pipeline.to_dict(), build_problem_reference(problem_id), random_seeds

def scan_pipeline_runs(pipeline_id):
   problem_ids, random_seeds = set(), set()

   pipeline_run_search = Search(using=CONNECTION, index='pipeline_runs') \
      .query('match', pipeline__id=pipeline_id) \
      .query('match', run__phase='PRODUCE') \
      .query('match', status__state='SUCCESS')
   if pipeline_run_search.count() != 1:
      return problem_ids, random_seeds

   for pipeline_run in pipeline_run_search.scan():
      random_seeds.add(pipeline_run.random_seed)
      problem_ids.add(pipeline_run.problem.id)
   return problem_ids, random_seeds

def query_generator(index: str, id: str=None):
   search = Search(using=CONNECTION, index=index)
   if id:
      search = search.query('match', id=id)
   for hit in search.scan():
      yield hit
