from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from tqdm import tqdm

HOST = 'https://metalearning.datadrivendiscovery.org/es'
CONNECTION = Elasticsearch(hosts=[HOST], timeout=300)

def find_pipelines(keyword: str, limit_indexes=False, limit_results=None):
   '''Queries the metalearning database for pipelines using the specified primitive

   Queries the metalearning database using the Elasticsearch endpoint documented
   on D3M's website (see https://metalearning.datadrivendiscovery.org for more
   info). Finds all pipelines containing a certain primitive as specified by the
   keyword argument. Also determines the index(es) of that primitive in each
   matching pipeline.
   
   Arguments
   ---------
   keyword : str
      A substring of a primitive's python path. If the pipeline has any
      primitive containing the keyword somewhere in the python path, that pipeline
      is a "hit". For example, if you want to find pipelines that contain the
      Common Profiler, set to 'profiler.Common'. To find pipelines that use any
      classification primitive, set to 'classification'.
   limit_indexes : 'first', 'last', or False (default)
      Limits which index of the primitive
      is returned for each pipeline match. Use 'first' to get the index of the
      first matching primitive specified by the keyword arg. Use 'last' to get
      the index of the last match. Use False (default) to get a list of all
      indexes for each pipeline specifying where the primitive is.
   limit_results : int or None (default)
      Specifies the max number of results that
      should be returned from a query. If 'None' then all matching queries will be
      returned. Note that if a number is specified, the same pipelines may or may
      not be returned when identical queries are issued due to the nondeterministic
      nature of the Elasticsearch API (it favors speed over ordered data).
   
   Returns
   -------
   A list of tuples where each tuple represents a matching pipeline and
   the index(es) of the desired primitives in the given pipeline's steps.
   '''

   # TODO check that the pipelines have pipeline runs
   #      check that the pipelines we return have run successfully

   if limit_indexes not in { 'first', 'last', False }:
      raise ValueError(f'Invalid value "{limit_indexes}" for arg limit_indexes')
   
   if limit_results is not None and type(limit_results) is not int:
      raise ValueError(f'limit_results must be set to None or a positive integer')
   
   wildcard_query = Q('wildcard', steps__primitive__python_path='*'+keyword+'*')
   nested_query = Q('nested', path='steps', query=wildcard_query)
   search = Search(using=CONNECTION, index='pipelines').query(nested_query)

   results = []
   descrip = f'Scanning {limit_results if limit_results else "all"} pipelines containing "{keyword}"'
   num_queries = limit_results if limit_results else search.count()
   with tqdm(descrip, total=num_queries) as progress:
      progress.set_description(desc=descrip)
      for hit in search.scan():
         if check_for_pipeline_runs(hit.id) <= 0:
            continue

         locs = [i for i, step in enumerate(hit.steps) if keyword in step['primitive']['python_path']]
         if limit_indexes == 'last':
            locs = locs[-1]
         elif limit_indexes == 'first':
            locs = locs[0]
         
         results.append((hit.to_dict(), locs))
         progress.update(1)

         if len(results) == limit_results:
            break

   return results


def check_for_pipeline_runs(pipeline_id: str):
   search = Search(using=CONNECTION, index='pipeline_runs') \
      .query('match', pipeline__id=pipeline_id) \
      .query('match', run__phase='PRODUCE') \
      .query('match', status__state='SUCCESS')

   return search.count()


