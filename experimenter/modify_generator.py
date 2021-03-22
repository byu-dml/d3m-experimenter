from experimenter.query import query_on_seeds
from experimenter import queue, utils
from experimenter.utils import download_from_database
import d3m.metadata.pipeline
from random import randint
from d3m.contrib.pipelines import K_FOLD_TABULAR_SPLIT_PIPELINE_PATH as data_split_file
import json
import yaml
from experimenter.evaluate_pipeline_new import evaluate_pipeline_on_problem as evaluate_pipeline

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
        if (args.test is True):
            self.query_results = self._run_seed_test(self.args)
        else:
            self.query_results = self._query(self.args)
        self.generator = self._get_generator()
            
    def __iter__(self):
        return self


    def __next__(self):
        #iterate through query results
        job = next(self.generator)
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
        for query_result in self.query_results:
            #iterate through modifier results
            for pipeline, problem_path, dataset_doc, random_seed, prep in self._modify(query_result,self.args):
                #save the pipeline to path and return pipeline path
                data_prep_pipeline, data_random_seed = prep
                pipeline_path = download_from_database(pipeline, type_to_download='Pipeline')
                if (data_prep_pipeline is not None):
                    data_prep_pipeline = download_from_database(data_prep_pipeline, type_to_download='Preparation')
                #catch error returning none for file paths or preparation pipeline
                #TODO get data preparation pipeline even when it is not explicitly defined
                if (problem_path is None or dataset_doc is None or data_prep_pipeline is None):     
                    continue
                evaluate_pipeline(pipeline_path=pipeline_path,
                                    problem_path=problem_path,
                                     input_path=dataset_doc,
                                     random_seed=random_seed,
                                     data_pipeline_path=data_prep_pipeline,
                                     data_random_seed=data_random_seed)
                job = queue.make_job(evaluate_pipeline,
                                     pipeline_path=pipeline_path,
                                     problem_path=problem_path,
                                     input_path=dataset_doc,
                                     random_seed=random_seed,
                                     data_pipeline_path=data_prep_pipeline,
                                     data_random_seed=data_random_seed)
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
            yield query_args['pipeline'], query_args['problem_path'], query_args['dataset_doc_path'], new_seed, (query_args['data_prep_pipeline'], query_args['data_prep_seed']) 
            
            
    def _run_seed_test(self,args):
        """ Test designed for development and functionality purposes.
            It uses and dataset and pipeline that is saved in d3m-experimenter
        """
        with open('experimenter/pipelines/bagging_classification.json', 'r') as pipeline_file:
            pipeline = json.load(pipeline_file) 
        dataset_path = utils.get_dataset_doc_path('185_baseball_MIN_METADATA_dataset')
        problem_path = utils.get_problem_path('185_baseball_MIN_METADATA_problem')
        data_prep_seed = 0
        with open(data_split_file, 'r') as pipeline_file:
            data_prep_pipeline = yaml.full_load(pipeline_file)
        data_prep_pipeline = data_prep_pipeline
        used_seeds = {2,15}
        yield {'pipeline': pipeline, 'problem_path': problem_path, 'dataset_doc_path': dataset_path, 
               'tested_seeds': used_seeds, 'data_prep_pipeline': 
               data_prep_pipeline, 'data_prep_seed': data_prep_seed}


    def _modify_swap_primitive(self, swap_pipeline, query_args):
        raise ValueError("No functionality for swapping primitives yet")
        
        
