from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from tqdm import tqdm
from experimenter.problem import ProblemReference
from experimenter.utils import get_problem_parent_dir

HOST = 'https://metalearning.datadrivendiscovery.org/es'
CONNECTION = Elasticsearch(hosts=[HOST], timeout=300)

def find_pipelines(primitive_id: str, limit_indexes=False, limit_results=None):
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
   limit_results : int or None (default)
      Specifies the max number of results that should be returned from a query.
      If 'None' then all matching queries will be returned. Note that if a number
      is specified, the same pipelines may or may not be returned when identical
      queries are issued due to the nondeterministic nature of the Elasticsearch
      API (it favors speed over ordered data).
   
   Returns
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
   
   if limit_results is not None and type(limit_results) is not int:
      raise ValueError(f'limit_results must be set to None or a positive integer')
   
   match_query = Q('match', steps__primitive__id=primitive_id)
   nested_query = Q('nested', path='steps', query=match_query)
   search = Search(using=CONNECTION, index='pipelines').query(nested_query)

   results = []
   primitive_descrip = '...' + '.'.join(get_primitive_python_path(primitive_id).split('.')[-3:])
   descrip = f'Scanning {limit_results if limit_results else "all"} pipelines containing "{primitive_descrip}"'
   num_queries = limit_results if limit_results else search.count()
   with tqdm(descrip, total=num_queries) as progress:
      progress.set_description(desc=descrip)
      for hit in search.scan():
         if check_for_pipeline_runs(hit.id) <= 0:
            continue

         datasets = get_datasets(hit.id)
         used_random_seeds = get_used_random_seeds(hit.id)

         locs = [i for i, step in enumerate(hit.steps) if primitive_id == step.primitive.id]
         if limit_indexes == 'last':
            locs = locs[-1]
         elif limit_indexes == 'first':
            locs = locs[0]
         
         results.append((hit.to_dict(), locs, datasets, used_random_seeds))
         progress.update(1)

         if len(results) == limit_results:
            break

   return results


def pipeline_generator(pipeline_id: str=None):
   pipeline_search = Search(using=CONNECTION, index='pipelines')
   if pipeline_id:
      pipeline_search = pipeline_search.query('match', id=pipeline_id)
   for pipeline in pipeline_search.scan():
      pipeline_run_search = Search(using=CONNECTION, index='pipeline_runs') \
         .query('match', pipeline__id=pipeline.id) \
         .query('match', run__phase='PRODUCE') \
         .query('match', status__state='SUCCESS')
      if pipeline_run_search.count() != 1:
         continue
      random_seeds = set()
      problem_ids = set()
      for pipeline_run in pipeline_run_search.scan():
         random_seeds.add(pipeline_run.random_seed)
         problem_ids.add(pipeline_run.problem.id)
      for problem_id in problem_ids:
         yield pipeline.to_dict(), build_problem_reference(problem_id), random_seeds


def build_problem_reference(problem_id: str):
   parent_dir = get_problem_parent_dir(problem_id)
   dir_id = parent_dir.split('/')[-1]
   enclosing_dir = '/'.join(parent_dir.split('/')[:-1])
   return ProblemReference(dir_id, '', enclosing_dir)


def get_pipeline(pipeline_id: str):
   '''Returns a pipeline and the datasets and random seeds used in its pipeline runs.
   '''
   search = Search(using=CONNECTION, index='pipelines').query('match', id=pipeline_id)
   if search.count() <= 0:
      return None, None, None
   hit = next(iter(search))
   return hit.to_dict(), get_datasets(hit.id), get_used_random_seeds(hit.id)


def check_for_pipeline_runs(pipeline_id: str):
   '''Returns the number of successful pipeline runs that a pipeline has.
   '''
   search = Search(using=CONNECTION, index='pipeline_runs') \
      .query('match', pipeline__id=pipeline_id) \
      .query('match', run__phase='PRODUCE') \
      .query('match', status__state='SUCCESS')

   return search.count()


def get_used_random_seeds(pipeline_id: str):
   '''Gets a set of random seeds used in a pipeline's successful
   pipeline runs.

   Arguments
   ---------
   pipeline_id : str
      The pipeline's unique id.

   Returns
   -------
   A set containing the random seeds that have already been used for
   pipeline runs on this pipeline.
   '''
   search = Search(using=CONNECTION, index='pipeline_runs') \
      .query('match', pipeline__id=pipeline_id) \
      .query('match', run__phase='PRODUCE') \
      .query('match', status__state='SUCCESS')
   
   random_seeds = set()
   for hit in search.scan():
      random_seeds.add(hit.random_seed)
   return random_seeds


def get_datasets(pipeline_id: str):
   '''Gets all datasets that have been used in pipeline runs with a given pipeline.

   Arguments
   ---------
   pipeline_id : str
      A pipeline's unique id.
   
   Returns
   -------
   A dictionary containing the datasets used in the pipeline's successful pipeline
   runs. Each key in the dictionary is the dataset's unique digest, and the value is
   the dataset's human-readable id string.
   '''
   search = Search(using=CONNECTION, index='pipeline_runs') \
      .query('match', pipeline__id=pipeline_id) \
      .query('match', run__phase='PRODUCE') \
      .query('match', status__state='SUCCESS')
   
   datasets = {}
   for hit in search.scan():
      datasets.update({dataset['digest']: dataset['id'] for dataset in hit.datasets})

   return datasets


def get_primitive_python_path(primitive_id: str):
   '''Gets a primitive's python path based on its unique id.
   '''
   search = Search(using=CONNECTION, index='primitives') \
      .query('match', id=primitive_id)
   
   return next(iter(search)).python_path


def get_primitive_id(primitive_python_path: str):
   '''Gets a primitive's unique id based on its python path.
   '''
   search = Search(using=CONNECTION, index='primitives') \
      .query('match', python_path=primitive_python_path)
   
   return next(iter(search)).id


def get_primitive(primitive_id: str):
   '''Get a primitive in dictionary form.

   **Warning, this function will be deprecated. Use d3m's get_primitive_by_id()
   to add a primitive to a pipeline instead.**

   Arguments
   ---------
   primitive_id : str
      A primitive's unique id.
   
   Returns
   -------
   A dictionary of the primitive.
   '''
   search = Search(using=CONNECTION, index='primitives') \
      .query('match', id=primitive_id)
   
   return next(iter(search)).to_dict()
