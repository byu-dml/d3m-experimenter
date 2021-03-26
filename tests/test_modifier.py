import unittest
from experimenter import modify_generator, queue, exceptions, utils
from experimenter.databases.d3m_mtl import D3MMtLDB
from d3m.contrib.pipelines import K_FOLD_TABULAR_SPLIT_PIPELINE_PATH
from d3m.contrib.pipelines import SCORING_PIPELINE_PATH as scoring_file

class GeneratorModifierTestCase(unittest.TestCase):
    
    
    def test_random_seed_modifier_job_count(self):
        #initialize the modifier with random-seed and a given max jobs
        args = {'seed_limit':35, 'submitter':None, 'pipeline_id':None}
        num_test = 5
        modifier = modify_generator.ModifyGenerator('random-seed', num_test, {'seed_limit':25})
        modifier.query_args = self.get_seed_test_args
        #start the counter to make sure there are the right amount of jobs
        counter = 0
        seed_old = 12.1
        #begin the test if number of jobs is correct
        for job in modifier:
           counter += 1
           _,_,seed_new = job
           self.assertNotEqual(seed_old, seed_new)
           seed_old = seed_new
        self.assertEqual(counter,num_test) 
      
        
    def test_query_random_seeds_set_size(self):
        args = {'seed_limit':25, 'submitter':'byu', 'pipeline_id':None}
        query_results = modify_generator.query_on_seeds(args['pipeline_id'], args['seed_limit'], args['submitter'])
        #test 10 query results
        for i in range(10):
            query = next(query_results)
            self.assertTrue(len(query['tested_seeds']) < seed_limit)   
          
       
    def test_d3m_interface_init(self):
        init_fail = False
        try:
            d3m_db = D3MMtLDB()
        except:
            init_fail = True
        self.assertFalse(init, "D3M Interface Failed")    
    
               
    def get_seed_test_args(self,args):
        """ returns args for testing modify generator random-seed
            functionality purposes.  It uses a dataset and pipeline 
            that is saved in the d3m-experimenter
        """
        with open('experimenter/pipelines/bagging_classification.json', 'r') as pipeline_file:
            pipeline = json.load(pipeline_file) 
        dataset_path = utils.get_dataset_doc_path('185_baseball_MIN_METADATA_dataset')
        problem_path = utils.get_problem_path('185_baseball_MIN_METADATA_problem')
        data_prep_seed = 0
        data_prep_seed = 0
        data_prep_pipeline = K_FOLD_TABULAR_SPLIT_PIPELINE_PATH
        scoring_pipeline = scoring_file
        scoring_seed = 0
        used_seeds = {2,15}
        yield {'pipeline': pipeline, 'problem_path': problem_path, 'dataset_doc_path': dataset_path, 
               'tested_seeds': used_seeds, 'data_prep_pipeline': data_prep_pipeline, 
               'data_prep_seed': data_prep_seed, 'data_params': None,
               'scoring_pipeline': scoring_pipeline, 'scoring_seed': scoring_seed,
               'scoring_params': None} 
            
              
if __name__ == '__main__':
    unittest.main()
