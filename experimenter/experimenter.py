
import logging
logger = logging.getLogger(__name__)
from random import sample
from .constants import models, preprocessors, problem_directories, blacklist_non_tabular_data
from d3m import index as d3m_index
from d3m import utils as d3m_utils
from d3m.primitive_interfaces.base import PrimitiveBase
from d3m.metadata.pipeline import PrimitiveStep
from d3m.metadata.base import Context, ArgumentType
from typing import List, Tuple
import logging
from d3m.metadata.pipeline import Pipeline
from experimenter.pipeline_builder import EZPipeline
import os
import json
from .database_communication import PipelineDB
from itertools import combinations
from bson import json_util
from d3m.metadata import base as metadata_base, problem as base_problem
from experimenter.pipeline_builder import add_pipeline_step, create_pipeline_step
from experimenter.experiments.metafeatures import MetafeatureExperimenter
from experimenter.experiments.random import RandomArchitectureExperimenter
from experimenter.experiments.straight import StraightArchitectureExperimenter
from experimenter.experiments.ensemble import EnsembleArchitectureExperimenter
from experimenter.experiments.stacked import StackedArchitectureExperimenter

from experimenter import utils


class Experimenter:
    """
    This class is initialized with all the paths info needed to find and create pipelines.
    It first finds all possible problems in the datasets_dir/problem_directories/* and then
    generates pipelines.  This class is used by the ExperimenterDriver class to run the pipelines.
    """

    def __init__(
        self,
        datasets_dir: str,
        volumes_dir: str,
        *,
        input_problem_directory=None,
        input_models=None,
        input_preprocessors=None,
        generate_pipelines=True,
        generate_problems=False,
        pipeline_folder=None,
        pipeline_gen_type: str = "straight",
        **experiment_args
    ):
        self.datasets_dir = datasets_dir
        self.volumes_dir = volumes_dir
        self.mongo_database = PipelineDB()

        # set up the primitives according to parameters
        self.preprocessors = preprocessors if input_preprocessors is None else input_preprocessors
        self.models = models if input_models is None else input_models
        self.problem_directories = problem_directories if input_problem_directory is None else input_problem_directory

        self.generated_pipelines = {}
        self.problems = {}
        self.incorrect_problem_types = {}

        self.experiments = {
            "metafeatures": MetafeatureExperimenter(),
            "random": RandomArchitectureExperimenter(),
            "straight": StraightArchitectureExperimenter(),
            "ensemble": EnsembleArchitectureExperimenter(),
            "stacked": StackedArchitectureExperimenter()
        }

        if generate_problems:
            logger.info("Generating problems...")
            self.problems = self.get_possible_problems()
            self.num_problems = len(self.problems["classification"]) + len(self.problems["regression"])

            logger.info("There are {} problems".format(self.num_problems))

        if generate_pipelines:            
            logger.info("Generating pipelines of type {}".format(pipeline_gen_type))

            if pipeline_gen_type not in self.experiments:
                raise Exception("Cannot parse generation type {}".format(pipeline_gen_type))
            
            experiment = self.experiments[pipeline_gen_type]
            self.generated_pipelines = experiment.generate_pipelines(
                preprocessors=self.preprocessors,
                models=self.models,
                **experiment_args
            )

            self.num_pipelines = len(self.generated_pipelines["classification"]) + len(self.generated_pipelines["regression"])

            logger.info("There are {} pipelines".format(self.num_pipelines))

            if pipeline_folder is None:
                self.mongo_database = PipelineDB()
                logger.info('Exporting pipelines to mongodb...')
                self.output_pipelines_to_mongodb()
            else:
                logger.info("Exporting pipelines to {}".format(pipeline_folder))
                self.output_values_to_folder(pipeline_folder)

    def get_possible_problems(self) -> dict:
        """
        The high level function to get all problems.  It seperates them into classification and regression problems and ignores the rest
        This function also adds the problem docs and dataset docs to our database if they do not already exist
        :return a dictionary containing two keys of file paths: `classification` and `regression`.  Each key is a list of file paths.
        """
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
                    logger.info("ERROR: failed to get dataset document: {}".format(e))

                problem_type = self.get_problem_type(dataset_name, [problem_description_path])
                if problem_type in problems_list:
                    problems_list[problem_type].append(os.path.join(datasets_dir, dataset_name))
        return problems_list

    def get_problem_type(self, problem_name: str, absolute_paths: List[str]):
        """
        Gathers the type of the problem from the name and path
        :param problem_name: the name of the problem to get the type of
        :param absolute_paths: the absolute_paths containing seed, LL0, and LL1 datasets
        """
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
            logger.info(e)
            return False

    def output_values_to_folder(self, location: str = "default"):
        """
        Exports pipelines files as json to a folder
        :param location: the path to export the files
        """
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
        logger.info("Pipeline json files exported to: {}".format(location))

    def output_pipelines_to_mongodb(self):
        """
        Writes pipelines to mongo, if they don't already exist
        """
        added_pipeline_sum = 0
        for pipeline_type in self.generated_pipelines:
            for pipe in self.generated_pipelines[pipeline_type]:
                added_pipeline_sum += self.mongo_database.add_to_pipelines_mongo(pipe)

        logger.info("Results: {} pipelines added. {} pipelines already exist in database".format(added_pipeline_sum,
                                                                               self.num_pipelines - added_pipeline_sum))
                                                                            
    def generate_default_pipeline(self) -> Pipeline:
        """
        Example from https://docs.datadrivendiscovery.org/devel/pipeline.html#pipeline-description-example
        :return: the sample pipeline
        """
        # Creating pipeline
        pipeline_description = EZPipeline(context=Context.TESTING)
        pipeline_description.add_input(name='inputs')

        # dataset_to_dataframe step
        add_pipeline_step(
            pipeline_description,
            'd3m.primitives.data_transformation.dataset_to_dataframe.Common',
            'inputs.0'
        )
        pipeline_description.set_step_i_of('raw_df')

        # column_parser step
        add_pipeline_step(
            pipeline_description,
            'd3m.primitives.data_transformation.column_parser.DataFrameCommon',
        )

        # extract_columns_by_semantic_types(attributes) step
        extract_attributes_step = create_pipeline_step(
            'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon',
            pipeline_description.curr_step_data_ref
        )
        extract_attributes_step.add_hyperparameter(name='semantic_types', argument_type=ArgumentType.VALUE,
                                  data=['https://metadata.datadrivendiscovery.org/types/Attribute'])
        pipeline_description.add_step(extract_attributes_step)
        pipeline_description.set_step_i_of('attrs')

        # extract_columns_by_semantic_types(targets) step
        extract_targets_step = create_pipeline_step(
            'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon',
            pipeline_description.data_ref_of('raw_df')
        )
        extract_targets_step.add_hyperparameter(name='semantic_types', argument_type=ArgumentType.VALUE,
                                  data=['https://metadata.datadrivendiscovery.org/types/TrueTarget'])
        pipeline_description.add_step(extract_targets_step)
        pipeline_description.set_step_i_of('target')

        # imputer step
        add_pipeline_step(
            pipeline_description,
            'd3m.primitives.data_cleaning.imputer.SKlearn',
            pipeline_description.data_ref_of('attrs')
        )

        # random_forest step
        rf_step = create_pipeline_step(
            'd3m.primitives.regression.random_forest.SKlearn',
            pipeline_description.curr_step_data_ref
        )
        rf_step.add_argument(
            name='outputs',
            argument_type=ArgumentType.CONTAINER,
            data_reference=pipeline_description.data_ref_of('target')
        )
        pipeline_description.add_step(rf_step)

        # Final Output
        pipeline_description.add_output(name='output predictions', data_reference=pipeline_description.curr_step_data_ref)

        # Output to YAML
        return {"classification": [pipeline_description], "regression": []}


def pretty_print_json(json_obj: str):
    """
    Pretty prints a JSON object to make it readable
    """
    import pprint
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(json_obj)
