import json
import tempfile
import unittest
 
from experimenter import d3m_utils, evaluate_pipeline_new

class D3mUtilsTestCases(unittest.TestCase):

    def test_create_output_run_filename(self):
        pipeline_path = 'data/pipelines/bagging_classification.json'
        problem_path = 'data/185_baseball/185_baseball_problem/problemDoc.json'
        input_path = 'data/185_baseball/185_baseball_dataset/datasetDoc.json'

        actual_output_run_filename = d3m_utils.create_output_run_filename(pipeline_path,
            problem_path, input_path)
        
        pipeline_digest = '990784f527a78250fcab70af9714314490e91f9a5916eb38834d74e8c38f435b'
        problem_digest = ''
        dataset_digest = 'ffdd21d61bc1c3bfd223248d5affd60d2a660d0ac1780fe4def26bb068dd541a'

        expected_output_run_filename = '_'.join([pipeline_digest,
            problem_digest, dataset_digest]) + '.json'

        self.assertEqual(actual_output_run_filename, expected_output_run_filename)

    def test_execute_d3m_cli(self):
        pipeline_path = 'data/pipelines/bagging_classification.json'
        problem_path = 'data/185_baseball/185_baseball_problem/problemDoc.json'
        input_path = 'data/185_baseball/185_baseball_dataset/datasetDoc.json'
        data_random_seed = 0
        
        import logging
        import sys
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

        log = logging.getLogger("TestLog")

        with tempfile.NamedTemporaryFile() as f:
            output_run_path = f.name
            args = evaluate_pipeline_new.create_runtime_evaluate_args(pipeline_path,
                problem_path, input_path, output_run_path, data_random_seed)

            log.debug(args)
            evaluate_pipeline_new.execute_d3m_cli(args, output_run_path)

            with open(output_run_path) as output_f:
               pipeline_run_state = json.load(output_f)['status']['state']

        self.assertEqual(pipeline_run_status, 'SUCCESS')
        
if __name__ == '__main__':
    unittest.main()
