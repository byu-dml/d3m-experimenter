from random import randint
import json
import os
import yaml

from d3m.contrib.pipelines import K_FOLD_TABULAR_SPLIT_PIPELINE_PATH
from d3m.contrib.pipelines import SCORING_PIPELINE_PATH as scoring_file

from experimenter import queue, utils, query
from experimenter.utils import download_from_database
from experimenter.runtime import evaluate


class ModifyGenerator:
    """ Generator to be used for creating modified pipelines based on existing
        pipelines in the database
    """
    def __init__(self, modify_type: str='random-seed', max_jobs: int=None, args=None):
        self.args = args
        #intialize commonly used variables
        self.modifier_type = modify_type
        self.max_jobs = max_jobs
        self.num_complete = 0
        #run the query on initializing to define the query results
        self.query_results = None


    def __iter__(self):
        return self


    def __next__(self):
        #iterate through query results
        job = next(self._get_generator())
        if (self.max_jobs):
            if (self.num_complete > self.max_jobs):
                raise StopIteration
        return job

             
    def _get_generator(self):
        """
        Main generator to be used of ModifyGenerator class
        Can only handle cases where there is a data preparation
        pipeline in the pipeline run
        """
        if (self.query_results is None):
            self.query_results = self._query(self.args)
        for query_result in self.query_results:
            #iterate through modifier results
            for pipeline, problem_path, dataset_doc, seed, data, score in self._modify(query_result,self.args):
                #save the pipeline to path and return pipeline path
                data_prep_pipeline, data_random_seed, data_params = data
                scoring_pipeline, scoring_random_seed, scoring_params = score
                pipeline_path = download_from_database(pipeline, type_to_download='pipelines')
                #TODO - catch when there is no data preparation pipeline and pass it further to evaluate
                #catch error returning none for file paths or preparation pipeline
                if (problem_path is None or dataset_doc is None or data_prep_pipeline is None):     
                    continue
                #check if query returned a path or an id
                if (os.path.exists(data_prep_pipeline) is False):
                    data_prep_pipeline = download_from_database(data_prep_pipeline, type_to_download='data-preparation-pipelines')
                if (os.path.exists(scoring_pipeline) is False):
                    scoring_pipeline = download_from_database(scoring_pipeline, type_to_download='scoring-pipelines')
                job = queue.make_job(evaluate,
                                     pipeline=pipeline_path,
                                     problem=problem_path,
                                     input=dataset_doc,
                                     random_seed=seed,
                                     data_pipeline=data_prep_pipeline,
                                     data_random_seed=data_random_seed,
                                     data_params=data_params,
                                     scoring_pipeline=scoring_pipeline,
                                     scoring_random_seed=scoring_random_seed,
                                     scoring_params=scoring_params)
                self.num_complete += 1
                yield job
        
        
    def _query(self, args):
        """method for querying database according to pipeline modification type
        """
        if (self.modifier_type=='random-seed'):
            return query_on_seeds(args.pipeline_id, args.seed_limit, args.submitter)
        if (self.modifier_type=='swap-primitive'):
            return query_on_primitive(args.primitive_id, args.limit_indeces)
        else:
            raise ValueError("This type of modification is not yet an option")
    
            
    def _modify(self, query_args: dict, args):
        """Handler for different types of pipeline modification tasks
        """
        if self.modifier_type=='random-seed':
            return self._modify_random_seed(args.seed_limit, query_args)
        if self.modifier_type=='swap-primitive':
            return self._modify_swap_primitive(args.swap_primitive_id, query_args)
        else:
            raise ValueError("This type of modification is not yet an option")
    
 
    def _check_for_duplicates(self, pipeline_to_check, problem_ref_to_check):
        """Pseudo function/method for duplicate checking 
            - This function is not complete and will be used for future generation type jobs
        """
        #create the pipeline to check for duplicates from the path
        pipeline_object = d3m.metadata.pipeline.Pipeline.from_json(pipeline_to_check)
        #query through the database for equal pipelines
        similar_pipeline_runs_in_database = query.generate_similar_pipeline_runs()
        for pipeline in similar_pipeline_runs_in_database:
            if (pipeline_object.equals(pipeline)):
                return True
        return False   
    
    
    def _modify_random_seed(self, seed_limit, query_args):
        """Generates new seeds for a given pipeline, problem, and dataset
           It is dependent on the seed limit for how many it will generate
        """
        used_seeds = query_args['tested_seeds']
        num_run = len(used_seeds)
        #run until the right number of seeds have been run
        while (num_run < seed_limit):
            new_seed = randint(1,100000)
            if (new_seed in used_seeds):
                continue
            num_run += 1
            used_seeds.add(new_seed)
            #yield the necessary job requirements
            yield (query_args['pipeline'], query_args['problem_path'], query_args['dataset_doc_path'], new_seed, 
                  (query_args['data_prep_pipeline'], query_args['data_prep_seed'], query_args['data_params']), 
                  (query_args['scoring_pipeline'], query_args['scoring_seed'], query_args['scoring_params'])) 


    def _modify_swap_primitive(self, swap_pipeline, query_args):
        raise ValueError("No functionality for swapping primitives yet")
        
        
def query_on_seeds(pipeline_id: str=None, limit: int=None, submitter: str='byu'):
    """
    Helper function for generating jobs to be used in the random-seed swapping 
    generator
    """
    arguments = {'id': pipeline_id, '_submitter': submitter}
    pipeline_search = query.match_query(index='pipelines', arguments=arguments)
    for pipeline in pipeline_search.scan():
        pipeline_run_query = query.scan_pipeline_runs(pipeline.id, submitter)
        pipeline = pipeline.to_dict()
        for run_tuple, pipeline_run_params in pipeline_run_query.items():
            #get the unqiue params from the params list
            unique_run_params = query.combine_unique_params(pipeline_run_params)
            #unpack values from tuple
            query_arg_dict = query.unpack_run_tuple_args(run_tuple)
            for params in unique_run_params:
                query_args = query_arg_dict.copy()
                query_args['data_params'] = params['data_params']
                query_args['scoring_params'] = params['scoring_params']
                query_args['tested_seeds'] = params['random_seeds']
                query_args['pipeline'] = pipeline    
                if limit and len(query_args['tested_seeds']) > limit:
                    continue
                yield query_args
