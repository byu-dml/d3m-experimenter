import tempfile
import unittest

from experimenter import evaluate_pipeline_new

class EvaluatePipelineTestCase(unittest.TestCase):

    def test_create_runtime_evaluate_args(self):
        pipeline_path = 'data/pipelines/bagging_classification.json'
        problem_path = 'data/185_baseball/185_baseball_problem/problemDoc.json'
        input_path = 'data/185_baseball/185_baseball_dataset/datasetDoc.json'
        data_random_seed = 0

        with tempfile.NamedTemporaryFile() as f:
            output_run_path = f.name
            actual_args = evaluate_pipeline_new.create_runtime_evaluate_args(pipeline_path,
                problem_path, input_path, output_run_path, data_random_seed)
            
            expected_args = ['d3m', 'runtime', 'evaluate',
                '--pipeline', pipeline_path, '--problem', problem_path,
                '--input', input_path, '--output-run', output_run_path,
                '--data-random-seed', data_random_seed]

        self.assertEqual(actual_args, expected_args)

    def test_create_runtime_evaluate_args_invalid_pipeline_path(self):
        pipeline_path = 'data/pipelines/nonexistent_pipeline.json'
        problem_path = 'data/185_baseball/185_baseball_problem/problemDoc.json'
        input_path = 'data/185_baseball/185_baseball_dataset/datasetDoc.json'
        data_random_seed = 0

        with tempfile.NamedTemporaryFile() as f:
            output_run_path = f.name

            with self.assertRaises(ValueError) as cm:
                evaluate_pipeline_new.create_runtime_evaluate_args(pipeline_path,
                    problem_path, input_path, output_run_path, data_random_seed)
            
            actual_error_message = str(cm.exception)

            expected_error_message = '({}) is not a file'.format(pipeline_path)

        self.assertEqual(actual_error_message, expected_error_message)

    def test_create_runtime_evaluate_args_invalid_problem_path(self):
        pipeline_path = 'data/pipelines/bagging_classification.json'
        problem_path = 'data/nonexistent_problem.json'
        input_path = 'data/185_baseball/185_baseball_dataset/datasetDoc.json'
        data_random_seed = 0

        with tempfile.NamedTemporaryFile() as f:
            output_run_path = f.name

            with self.assertRaises(ValueError) as cm:
                evaluate_pipeline_new.create_runtime_evaluate_args(pipeline_path,
                    problem_path, input_path, output_run_path, data_random_seed)
            
            actual_error_message = str(cm.exception)

            expected_error_message = '({}) is not a file'.format(problem_path)

        self.assertEqual(actual_error_message, expected_error_message)

    def test_create_runtime_evaluate_args_invalid_input_path(self):
        pipeline_path = 'data/pipelines/bagging_classification.json'
        problem_path = 'data/185_baseball/185_baseball_problem/problemDoc.json'
        input_path = 'data/nonexistent_dataset.json'
        data_random_seed = 0

        with tempfile.NamedTemporaryFile() as f:
            output_run_path = f.name

            with self.assertRaises(ValueError) as cm:
                evaluate_pipeline_new.create_runtime_evaluate_args(pipeline_path,
                    problem_path, input_path, output_run_path, data_random_seed)
            
            actual_error_message = str(cm.exception)

            expected_error_message = '({}) is not a file'.format(input_path)

        self.assertEqual(actual_error_message, expected_error_message)
if __name__ == '__main__':
    unittest.main()
