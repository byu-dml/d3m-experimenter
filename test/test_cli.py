import unittest

from experimenter_driver import get_cli_args


class TestCLI(unittest.TestCase):
    def test_ensemble_args(self):
        """
        Tests correct parsing of arguments specific to the ensemble experimenter. 
        """
        ensemble_args = ["-p", "ensemble", "-nc", "3", "-npre", "1"]
        args = get_cli_args(ensemble_args)

        self.assertEqual(args.pipeline_gen_type, "ensemble")
        self.assertEqual(args.n_classifiers, 3)
        self.assertEqual(args.n_preprocessors, 1)

    def test_random_args(self):
        """
        Tests correct parsing of arguments specific to the random experimenter. 
        """
        random_args = [
            "-npipes",
            "100",
            "-dsr",
            "1",
            "10",
            "-mwsr",
            "1",
            "5",
            "-misr",
            "1",
            "4",
            "-mcf",
            "24",
        ]
        args = get_cli_args(random_args)

        self.assertEqual(args.n_pipelines, 100)
        self.assertEqual(args.depth_sample_range, [1, 10])
        self.assertEqual(args.max_width_sample_range, [1, 5])
        self.assertEqual(args.max_inputs_sample_range, [1, 4])
        self.assertEqual(args.max_complexity_factor, 24)
