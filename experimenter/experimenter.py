import argparse
import collections
import warnings

from bson import json_util
from .constants import models, preprocessors, problem_directories, blacklist_non_tabular_data, not_working_preprocessors
from d3m import index
from d3m.primitive_interfaces.base import PrimitiveBase
from d3m.metadata.pipeline import PrimitiveStep
from d3m.metadata.base import Context, ArgumentType
from typing import List
import logging
from d3m.metadata.pipeline import Pipeline
import glob
import os
import json
import sys
from .database_communication import PipelineDB

from experimenter import utils

logger = logging.getLogger(__name__)


class Experimenter:
    """
    This class is initialized with all the paths info needed to find and create pipelines.
    It first finds all possible problems in the datasets_dir/problem_directories/* and then
    generates pipelines.  This class is used by the ExperimenterDriver class to run the pipelines.
    @:param input_models: a dictionary of two items, "classification" and "regression", each a list of primitive machine
    learning models
    """

    def __init__(self, datasets_dir: str, volumes_dir: str, pipeline_path: str, input_problem_directory=None,
                 input_models=None, input_preprocessors=None, generate_pipelines=True,
                 location=None, generate_problems=False):
        self.datasets_dir = datasets_dir
        self.volumes_dir = volumes_dir
        self.pipeline_path = pipeline_path
        self.mongo_database = PipelineDB()

        # set up the primitives according to parameters
        self.preprocessors = preprocessors if input_preprocessors is None else input_preprocessors
        self.models = models if input_models is None else input_models
        self.problem_directories = problem_directories if input_problem_directory is None else input_problem_directory

        self.generated_pipelines = {}
        self.problems = {}
        self.incorrect_problem_types = {}

        if generate_problems:
            print("Generating problems...")
            self.problems = self.get_possible_problems()
            self.num_problems = len(self.problems["classification"]) + len(self.problems["regression"])

            print("There are {} problems".format(self.num_problems))

        if generate_pipelines:
            print("Generating pipelines...")
            self.generated_pipelines: dict = self.generate_pipelines(self.preprocessors,
                                                                               self.models)
            self.num_pipelines = len(self.generated_pipelines["classification"]) + \
                                 len(self.generated_pipelines["regression"])

            print("There are {} pipelines".format(self.num_pipelines))

            if location is None:
                print('Exporting pipelines to mongodb...')
                self.output_pipelines_to_mongodb()
            else:
                print("Exporting pipelines to {}".format(location))
                self.output_values_to_folder(location)

    """
    Pretty prints a JSON object to make it readable
    """
    def _pretty_print_json(self, json):
        import pprint
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(json)

    """
    :param pipeline_description: an empty pipeline object that we can add steps to.
    :param step_counter: a integer representing the number of the next step we are on.
    :return pipeline_description: a Pipeline object that contains the initial steps to being a pipeline
    """
    def _add_initial_steps(self, pipeline_description: Pipeline, step_counter):

        # Creating pipeline
        pipeline_description.add_input(name='inputs')

        # TODO: decide when to use this
        # # Step 0: Denormalize - not required
        # denormalizer: PrimitiveBase = index.get_primitive("d3m.primitives.data_transformation.denormalize.Common")
        # step_0 = PrimitiveStep(primitive_description=denormalizer.metadata.query())
        # step_0.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='steps.{}.produce'.format(step_counter - 1))
        # step_0.add_output('produce')
        # pipeline_description.add_step(step_0)
        # step_counter += 1

        # Step 1: dataset_to_dataframe
        step_1 = PrimitiveStep(
            primitive=index.get_primitive('d3m.primitives.data_transformation.dataset_to_dataframe.Common'))
        step_1.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='inputs.0')
        step_1.add_output('produce')
        pipeline_description.add_step(step_1)
        step_counter += 1

        # Step 2: column_parser
        step_2 = PrimitiveStep(
            primitive=index.get_primitive('d3m.primitives.data_transformation.column_parser.DataFrameCommon'))
        step_2.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER,
                            data_reference='steps.{}.produce'.format(step_counter - 1))
        step_2.add_output('produce')
        pipeline_description.add_step(step_2)
        step_counter += 1

        # Step 3: Imputer
        sk_imputer: PrimitiveBase = index.get_primitive("d3m.primitives.data_preprocessing.random_sampling_imputer.BYU")
        step_3 = PrimitiveStep(primitive_description=sk_imputer.metadata.query())
        step_3.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER,
                            data_reference = 'steps.{}.produce'.format(step_counter - 1))
        step_3.add_output('produce')
        pipeline_description.add_step(step_3)
        step_counter += 1

        return step_counter

    def _add_predictions_constructor(self, pipeline_description, step_counter):
        # Step 6: PredictionsConstructor
        predictions_constructor: PrimitiveBase = index.get_primitive("d3m.primitives.data_transformation.construct_predictions.DataFrameCommon")
        step_6 = PrimitiveStep(primitive_description=predictions_constructor.metadata.query())
        step_6.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='steps.{}.produce'.format(step_counter - 1))
        step_6.add_argument(name='reference', argument_type=ArgumentType.CONTAINER, data_reference='steps.2.produce')
        step_6.add_output('produce')
        pipeline_description.add_step(step_6)
        step_counter += 1

        return step_counter

    def _get_required_args(self, p: PrimitiveBase):
        required_args = []
        metadata_args = p.metadata.to_json_structure()['primitive_code']['arguments']
        for arg, arg_info in metadata_args.items():
            if 'default' not in arg_info and arg_info['kind'] == 'PIPELINE':  # If yes, it is a required argument
                required_args.append(arg)
        return required_args

    def _generate_standard_pipeline(self, preprocessor: PrimitiveBase, classifier: PrimitiveBase):
        step_counter = 0

        # Creating Pipeline
        pipeline_description = Pipeline(context=Context.TESTING)

        step_counter = self._add_initial_steps(pipeline_description, step_counter)

        # Step 4: Preprocessor
        if preprocessor:
            step_4 = PrimitiveStep(primitive_description=preprocessor.metadata.query())
            for arg in self._get_required_args(preprocessor):
                step_4.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference='steps.{}.produce'.format(step_counter - 1))
            step_4.add_hyperparameter(name='use_semantic_types', argument_type=ArgumentType.VALUE, data=True)
            step_4.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="replace")
            step_4.add_output('produce')
            pipeline_description.add_step(step_4)
            step_counter += 1

        # Step 5: Classifier
        step_5 = PrimitiveStep(primitive_description=classifier.metadata.query())
        for index, arg in enumerate(self._get_required_args(classifier)):
            step_5.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                data_reference='steps.{}.produce'.format(step_counter - 1))
        step_5.add_hyperparameter(name='use_semantic_types', argument_type=ArgumentType.VALUE, data=True)
        step_5.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="replace")
        step_5.add_output('produce')
        pipeline_description.add_step(step_5)
        step_counter += 1

        step_counter = self._add_predictions_constructor(pipeline_description, step_counter)

        # Adding output step to the pipeline
        pipeline_description.add_output(name='Output', data_reference='steps.{}.produce'.format(step_counter - 1))

        return pipeline_description

    def get_possible_problems(self):
        problems_list = {"classification": [], "regression": []}
        for problem_directory in self.problem_directories:
            datasets_dir = os.path.join(self.datasets_dir, problem_directory)
            for dataset_name in os.listdir(datasets_dir):
                problem_description_path = utils.get_problem_path(dataset_name, datasets_dir)
                try:
                    # add to dataset collection if it hasn't been already
                    dataset_doc = utils.get_dataset_doc(dataset_name, datasets_dir)
                    self.mongo_database.add_to_datasets(dataset_doc)
                except Exception as e:
                    print("ERROR: failed to get dataset document: {}".format(e))

                problem_type = self.get_problem_type(dataset_name, [problem_description_path])
                if problem_type in problems_list:
                    problems_list[problem_type].append(os.path.join(datasets_dir, dataset_name))
        return problems_list

    def generate_pipelines(self, preprocessors: List[str], models: dict):
        preprocessors = list(set(preprocessors))

        generated_pipelines = {"classification": [], "regression": []}
        for type_name, model_list in models.items():
            # Generate all pipelines without preprocessors
            for model in model_list:
                predictor: PrimitiveBase = index.get_primitive(model)
                pipeline_without_preprocessor: Pipeline = self._generate_standard_pipeline(None, predictor)
                generated_pipelines[type_name].append(pipeline_without_preprocessor)

            # Generate all pipelines with preprocessors
            for p in preprocessors:
                preprocessor: PrimitiveBase = index.get_primitive(p)
                for model in model_list:
                    predictor: PrimitiveBase = index.get_primitive(model)

                    pipeline_with_preprocessor: Pipeline = self._generate_standard_pipeline(preprocessor, predictor)
                    generated_pipelines[type_name].append(pipeline_with_preprocessor)

        return generated_pipelines

    def get_problem_type(self, problem_name, absolute_paths):
        if problem_name in blacklist_non_tabular_data:
            return "skip"

        # problem is tabular, continue
        try:
            for path in absolute_paths:
                with open(path, 'r') as file:
                    problem_doc = json.load(file)
                    if problem_doc['about']['taskType'] == 'classification':
                        # add the problem doc to the database if it hasn't already
                        self.mongo_database.add_to_problems(problem_doc)
                        return "classification"
                    elif problem_doc['about']['taskType'] == 'regression':
                        self.mongo_database.add_to_problems(problem_doc)
                        return "regression"
                    else:
                        try:
                            self.incorrect_problem_types[problem_name] = [problem_doc['about']['taskType'],
                                                                          problem_doc['about']['taskSubType']]
                        except KeyError as e:
                            # some problems don't have a taskSubType, try again
                            self.incorrect_problem_types[problem_name] = [problem_doc['about']['taskType']]
                        return False
        except Exception as e:
            print(e)
            return False

    def output_values_to_folder(self, location="default"):
        if location == "default":
            location = "experimenter/created_pipelines/"
        # Write the pipeline to a file for the runtime
        for pipeline_type in self.generated_pipelines:
            for pipe in self.generated_pipelines[pipeline_type]:
                pipe_json = pipe.to_json_structure()
                output_path = location + pipeline_type + "_" + pipe_json['steps'][-2]['primitive']['python_path'] +\
                              pipe_json["id"] + ".json"
                with open(output_path, 'w') as write_file:
                    write_file.write(pipe.to_json(indent=4, sort_keys=True, ensure_ascii=False))
        print("Pipeline json files exported to: {}".format(location))

    def output_pipelines_to_mongodb(self):
        added_pipeline_sum = 0
        for pipeline_type in self.generated_pipelines:
            for pipe in self.generated_pipelines[pipeline_type]:
                added_pipeline_sum += self.mongo_database.add_to_pipelines_mongo(pipe)

        print("Results: {} pipelines added. {} pipelines already exist in database".format(added_pipeline_sum,
                                                                               self.num_pipelines - added_pipeline_sum))
