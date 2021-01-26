import unittest
from experimenter import modify_generator, queue, exceptions, utils
from query import query_on_seeds

class ModifierTestCase(unittest.TestCase):
    
    def test_seed_modifier(self):
        #initialize the modifier with random-seed and a given max jobs
        args = {'seed_limit':25, 'submitter':None, 'pipeline_id':None}
        num_test = 21
        modifier = modify_generator.ModifyGenerator('random-seed', num_test, {'seed_limit':25})
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
        
    def test_query_seeds(self):
        args = {'seed_limit':25, 'submitter':'byu', 'pipeline_id':None}
        query_results = query_on_seeds(args.pipeline_id, args.seed_limit, args.submitter)
        #test 10 query results
        for i in range(10):
            _,_,seed_list = next(query_results)
            self.assertTrue(len(seed_list) < seed_limit)    
    
if __name__ == '__main__':
    unittest.main()
