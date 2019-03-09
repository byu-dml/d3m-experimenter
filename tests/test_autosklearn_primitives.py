import json
import unittest

from d3m import index as d3m_index, runtime as runtime_module, utils as d3m_utils
from d3m.metadata import base as metadata_base

from experimenter import utils
from experimenter.autosklearn import (
    get_classification_pipeline as get_autosklearn_classification_pipeline
)
from experimenter.autosklearn.primitives import AutoSklearnClassifierPrimitive, Hyperparams


TEST_DATASET_NAME = 'LL0_1008_analcatdata_reviewer'

# AutoSklearnClassifierPrimitive.metadata.contribute_to_class(AutoSklearnClassifierPrimitive)


class AutoSklearnClassifierPrimitiveTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with d3m_utils.silence():
            d3m_index.register_primitive(
                AutoSklearnClassifierPrimitive.metadata.query()['python_path'],
                AutoSklearnClassifierPrimitive
            )

        cls.dataset_doc_path = utils.get_dataset_doc_path(TEST_DATASET_NAME)
        cls.problem_path = utils.get_problem_path(TEST_DATASET_NAME)
        cls.pipeline_description = get_autosklearn_classification_pipeline()

    def test_instantiation(self):
        try:
            AutoSklearnClassifierPrimitive(hyperparams=Hyperparams.defaults())
        except Exception as e:
            self.fail(str(e))

    def test_pipeline(self):
        dataset = runtime_module.get_dataset(self.dataset_doc_path)
        problem = utils.get_problem(self.problem_path)
        runtime = runtime_module.Runtime(
            self.pipeline_description, problem_description=problem,
            context=metadata_base.Context.TESTING, is_standard_pipeline=True
        )

        result = runtime.fit([dataset], return_values=['outputs.0'])
        try:
            result.check_success()
        except Exception as e:
            self.fail(str(e))
