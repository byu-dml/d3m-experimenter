import logging
import os
from collections import defaultdict
import typing as t

from d3m.metadata.base import Context
from d3m.metadata.pipeline import Pipeline

from experimenter.pipeline_builder import EZPipeline
from experimenter.databases.aml_mtl import PipelineDB
from experimenter.experiments.metafeatures import MetafeatureExperimenter
from experimenter.experiments.random import RandomArchitectureExperimenter
from experimenter.experiments.straight import StraightArchitectureExperimenter
from experimenter.experiments.ensemble import EnsembleArchitectureExperimenter
from experimenter.experiments.stacked import StackedArchitectureExperimenter
from experimenter.problem import ProblemReference
from experimenter.constants import (
    models,
    preprocessors,
    problem_directories,
    blacklist_non_tabular_data,
)
from experimenter.databases.d3m_mtl import D3MMtLDB


logger = logging.getLogger(__name__)


class Experimenter:
    """
    This class is initialized with all the paths info needed to find and create
    pipelines. It first finds all possible problems in the
    `datasets_dir/problem_directories/*` and then generates pipelines. This class
    is used by the `ExperimenterDriver` class to run the pipelines.
    """

    def __init__(
        self,
        datasets_dir: str,
        volumes_dir: str,
        *,
        input_problem_directories: list = None,
        input_models=None,
        input_preprocessors=None,
        generate_pipelines=True,
        generate_problems=False,
        pipeline_folder=None,
        pipeline_gen_type: str = "straight",
        verbose: bool = False,
        **experiment_args,
    ):
        self.datasets_dir = datasets_dir
        self.volumes_dir = volumes_dir
        self.mongo_database = PipelineDB()

        if verbose:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.CRITICAL)

        # set up the primitives according to parameters
        self.preprocessors = (
            preprocessors if input_preprocessors is None else input_preprocessors
        )
        self.models = models if input_models is None else input_models
        self.problem_directories = (
            problem_directories
            if input_problem_directories is None
            else input_problem_directories
        )

        self.generated_pipelines = {}
        self.problems = {}
        self.incorrect_problem_types = defaultdict(set)

        self.experiments = {
            "metafeatures": MetafeatureExperimenter(),
            "random": RandomArchitectureExperimenter(),
            "straight": StraightArchitectureExperimenter(),
            "ensemble": EnsembleArchitectureExperimenter(),
            "stacked": StackedArchitectureExperimenter(),
        }

        if generate_problems:
            logger.info("Generating problems...")
            self.problems = self.get_possible_problems()
            self.num_problems = len(self.problems["classification"]) + len(
                self.problems["regression"]
            )

            logger.info("There are {} problems".format(self.num_problems))

        if generate_pipelines:
            logger.info("Generating pipelines of type {}".format(pipeline_gen_type))

            if pipeline_gen_type not in self.experiments:
                raise Exception(
                    "Cannot parse generation type {}".format(pipeline_gen_type)
                )

            experiment = self.experiments[pipeline_gen_type]
            self.generated_pipelines = experiment.generate_pipelines(
                preprocessors=self.preprocessors, models=self.models, **experiment_args
            )

            self.num_pipelines = len(self.generated_pipelines["classification"]) + len(
                self.generated_pipelines["regression"]
            )

            logger.info("There are {} pipelines".format(self.num_pipelines))

            if pipeline_folder is None:
                logger.info("Exporting pipelines to mongodb...")
                self.output_pipelines_to_mongodb()
            else:
                logger.info("Exporting pipelines to {}".format(pipeline_folder))
                self.output_values_to_folder(pipeline_folder)

    def get_possible_problems(self) -> t.Dict[str, ProblemReference]:
        """
        The high level function to get all problems.  It seperates them into
        classification and regression problems and ignores the rest. This function
        also adds the problem docs and dataset docs to our database if they do not
        already exist.
        
        :return: a dictionary containing two keys: `classification`
            and `regression`.  Each key maps to a list of problems.
        """
        problems_list = {"classification": [], "regression": []}

        for problem_directory in self.problem_directories:
            datasets_dir = os.path.join(self.datasets_dir, problem_directory)

            for dataset_name in os.listdir(datasets_dir):
                if dataset_name in blacklist_non_tabular_data:
                    continue
                logger.info(f"processing problem: {datasets_dir}/{dataset_name}...")
                problem = ProblemReference(
                    dataset_name, problem_directory, self.datasets_dir
                )
                if problem.problem_type in problems_list:
                    problems_list[problem.problem_type].append(problem)
                else:
                    self.incorrect_problem_types[problem.name].update(
                        problem.task_keywords
                    )
        return problems_list

    def save_all_problems_to_d3m(self) -> None:
        d3m_db = D3MMtLDB()
        for problem_list in self.get_possible_problems().values():
            for problem in problem_list:
                # Add the dataset and problem to the database if they haven't
                # been already.
                d3m_db.save_dataset(problem)
                d3m_db.save_problem(problem)

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
                output_path = (
                    location
                    + pipeline_type
                    + "_"
                    + pipe_json["steps"][-2]["primitive"]["python_path"]
                    + pipe_json["id"]
                    + ".json"
                )
                with open(output_path, "w") as write_file:
                    write_file.write(
                        pipe.to_json(indent=4, sort_keys=True, ensure_ascii=False)
                    )
        logger.info("Pipeline json files exported to: {}".format(location))

    def output_pipelines_to_mongodb(self):
        """
        Writes pipelines to mongo, if they don't already exist.
        """
        added_pipeline_sum = 0
        for pipeline_type in self.generated_pipelines:
            for pipe in self.generated_pipelines[pipeline_type]:
                added_pipeline_sum += self.mongo_database.add_to_pipelines_mongo(pipe)

        logger.info(
            f"Results: {added_pipeline_sum} pipelines added. "
            f"{self.num_pipelines - added_pipeline_sum} pipelines already exist in "
            "database"
        )

    def generate_default_pipeline(self) -> Pipeline:
        """
        Example from https://docs.datadrivendiscovery.org/devel/pipeline.html#pipeline-description-example
        :return: the sample pipeline
        """
        # Creating pipeline
        pipeline_description = EZPipeline(context=Context.TESTING)
        pipeline_description.add_input(name="inputs")

        # dataset_to_dataframe step
        pipeline_description.add_primitive_step(
            "d3m.primitives.data_transformation.dataset_to_dataframe.Common", "inputs.0"
        )
        pipeline_description.set_step_i_of("raw_df")

        # column_parser step
        pipeline_description.add_primitive_step(
            "d3m.primitives.data_transformation.column_parser.Common",
        )

        # extract_columns_by_semantic_types(attributes) step
        pipeline_description.add_primitive_step(
            "d3m.primitives.data_transformation.extract_columns_by_semantic_types.Common",
            value_hyperparams={
                "semantic_types": [
                    "https://metadata.datadrivendiscovery.org/types/Attribute"
                ]
            },
        )
        pipeline_description.set_step_i_of("attrs")

        # extract_columns_by_semantic_types(targets) step
        pipeline_description.add_primitive_step(
            "d3m.primitives.data_transformation.extract_columns_by_semantic_types.Common",
            pipeline_description.data_ref_of("raw_df"),
            value_hyperparams={
                "semantic_types": [
                    "https://metadata.datadrivendiscovery.org/types/TrueTarget"
                ]
            },
        )
        pipeline_description.set_step_i_of("target")

        # imputer step
        pipeline_description.add_primitive_step(
            "d3m.primitives.data_cleaning.imputer.SKlearn",
            pipeline_description.data_ref_of("attrs"),
        )

        # random_forest step
        pipeline_description.add_primitive_step(
            "d3m.primitives.regression.random_forest.SKlearn"
        )

        # Final Output
        pipeline_description.add_output(
            name="output predictions",
            data_reference=pipeline_description.curr_step_data_ref,
        )

        # Output to YAML
        return {"classification": [pipeline_description], "regression": []}


def pretty_print_json(json_obj: str):
    """
    Pretty prints a JSON object to make it readable
    """
    import pprint

    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(json_obj)
