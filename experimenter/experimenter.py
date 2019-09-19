
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
from experimenter.autosklearn.pipelines import get_classification_pipeline, AutoSklearnClassifierPrimitive
from experimenter.pipeline_builder import add_pipeline_step, create_pipeline_step

from experimenter import utils


class Experimenter:
    """
    This class is initialized with all the paths info needed to find and create pipelines.
    It first finds all possible problems in the datasets_dir/problem_directories/* and then
    generates pipelines.  This class is used by the ExperimenterDriver class to run the pipelines.
    """

    def __init__(self, datasets_dir: str, volumes_dir: str, input_problem_directory=None,
                 input_models=None, input_preprocessors=None, generate_pipelines=True, args: dict = None,
                 location=None, generate_problems=False, generate_automl_pipelines=False):
        self.datasets_dir = datasets_dir
        self.volumes_dir = volumes_dir
        self.mongo_database = PipelineDB()

        # If we want to run automl systems, don't run regular pipelines
        if generate_automl_pipelines:
            generate_pipelines = False

        # set up the primitives according to parameters
        self.preprocessors = preprocessors if input_preprocessors is None else input_preprocessors
        self.models = models if input_models is None else input_models
        self.problem_directories = problem_directories if input_problem_directory is None else input_problem_directory

        self.generated_pipelines = {}
        self.problems = {}
        self.incorrect_problem_types = {}

        if generate_problems:
            logger.info("Generating problems...")
            self.problems = self.get_possible_problems()
            self.num_problems = len(self.problems["classification"]) + len(self.problems["regression"])

            logger.info("There are {} problems".format(self.num_problems))

        if generate_pipelines:
            logger.info("Generating pipelines of type {}".format(args.pipeline_gen_type))
            if args.pipeline_gen_type == "metafeatures":
                self.generated_pipelines: dict = self.generate_metafeatures_pipeline()
            elif args.pipeline_gen_type == "random":
                raise NotImplementedError("Random has not been implemented") # TODO: add random search
            elif args.pipeline_gen_type == "straight":
                self.generated_pipelines: dict = self.generate_pipelines(self.preprocessors, self.models)
            elif args.pipeline_gen_type == "ensemble":
                self.generated_pipelines: dict = self._wrap_generate_all_ensembles(k_ensembles=args.n_classifiers, p_preprocessors=args.n_preprocessors)
            else:
                raise Exception("Cannot parse generation type {}".format(args.pipeline_gen_type))

            self.num_pipelines = len(self.generated_pipelines["classification"]) + len(self.generated_pipelines["regression"])

            logger.info("There are {} pipelines".format(self.num_pipelines))

            if location is None:
                self.mongo_database = PipelineDB()
                logger.info('Exporting pipelines to mongodb...')
                self.output_pipelines_to_mongodb()
            else:
                logger.info("Exporting pipelines to {}".format(location))
                self.output_values_to_folder(location)

        if generate_automl_pipelines:
            self.generated_pipelines = self.generate_baseline_pipelines()
            self.num_pipelines = len(self.generated_pipelines["classification"])
            self.output_automl_pipelines_to_mongodb()

    def _add_initial_steps(self, pipeline_description: EZPipeline) -> None:
        """
        :param pipeline_description: an empty pipeline object that we can add
            the initial data preparation steps to.
        """
        # Creating pipeline
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
            'd3m.primitives.data_transformation.column_parser.DataFrameCommon'
        )

        # imputer step
        add_pipeline_step(
            pipeline_description,
            'd3m.primitives.data_preprocessing.random_sampling_imputer.BYU'
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

    def _add_predictions_constructor(self, pipeline_description: EZPipeline, input_data_ref: str = None) -> None:
        """
        Adds the predictions constructor to a pipeline description and increments the step counter
        :param pipeline_description: the pipeline-to-be
        :param input_data_ref: the data reference to be used as the input to the predictions primitive.
            If `None`, the output data reference to the pipeline's most recently added step will be used. 
        """
        if input_data_ref is None:
            input_data_ref = pipeline_description.curr_step_data_ref
        # PredictionsConstructor step
        step = create_pipeline_step(
            "d3m.primitives.data_transformation.construct_predictions.DataFrameCommon",
            input_data_ref
        )
        step.add_argument(
            name='reference',
            argument_type=ArgumentType.CONTAINER,
            data_reference=pipeline_description.data_ref_of('raw_df')
        )
        pipeline_description.add_step(step)

    def _get_required_args(self, p: PrimitiveBase) -> list:
        """
        Gets the required arguments for a primitive
        :param p: the primitive to get arguments for
        :return a list of the required args
        """
        required_args = []
        metadata_args = p.metadata.to_json_structure()['primitive_code']['arguments']
        for arg, arg_info in metadata_args.items():
            if 'default' not in arg_info and arg_info['kind'] == 'PIPELINE':  # If yes, it is a required argument
                required_args.append(arg)
        return required_args

    def _generate_standard_pipeline(self, preprocessor: PrimitiveBase, classifier: PrimitiveBase) -> Pipeline:
        """
        Adds the crucial preprocess or classifier steps to a basic pipeline description and returns the pipeline
        :param preprocessor: the primitive to use as a preprocessor
        :param classifier: the primitive to use as a classifier
        :return a newly created pipeline
        """

        # Creating Pipeline
        pipeline_description = EZPipeline(context=Context.TESTING)

        self._add_initial_steps(pipeline_description)
        preprocessor_used = False

        # Preprocessor Step
        if preprocessor:
            preprocessor_step = PrimitiveStep(primitive_description=preprocessor.metadata.query())
            for arg in self._get_required_args(preprocessor):
                if arg == "outputs":
                    data_ref = pipeline_description.data_ref_of('target')
                else:
                    data_ref = pipeline_description.data_ref_of('attrs')
                    preprocessor_used = True

                preprocessor_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=data_ref)
            preprocessor_step.add_hyperparameter(name='use_semantic_types', argument_type=ArgumentType.VALUE, data=True)
            preprocessor_step.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="replace")
            preprocessor_step.add_output('produce')
            pipeline_description.add_step(preprocessor_step)

        # Classifier Step
        classifier_step = PrimitiveStep(primitive_description=classifier.metadata.query())
        for arg in self._get_required_args(classifier):
            if arg == "outputs":
                data_ref = pipeline_description.data_ref_of('target')
            else:
                if preprocessor_used:
                    data_ref = pipeline_description.curr_step_data_ref
                else:
                    data_ref = pipeline_description.data_ref_of('attrs')
            classifier_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                data_reference=data_ref)
        classifier_step.add_hyperparameter(name='use_semantic_types', argument_type=ArgumentType.VALUE, data=True)
        classifier_step.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="replace")
        classifier_step.add_output('produce')
        pipeline_description.add_step(classifier_step)

        self._add_predictions_constructor(pipeline_description)

        # Adding output step to the pipeline
        pipeline_description.add_output(name='Output', data_reference=pipeline_description.curr_step_data_ref)

        return pipeline_description

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

    def generate_pipelines(self, preprocessors: List[str], models: dict) -> dict:
        """
        A high level function to create numerous pipelines for a list of preprocessor and model
        :param preprocessors: a list of preprocessors to generate pipelines with
        :param models: a dict containing two keys of `classification` and `regression` each with a list of model primitive names
        :return a dict containing two keys of `classification` and `regression` each a list of pipeline objects
        """
        preprocessors = list(set(preprocessors))

        generated_pipelines = {"classification": [], "regression": []}
        for type_name, model_list in models.items():
            # Generate all pipelines without preprocessors
            for model in model_list:
                predictor: PrimitiveBase = d3m_index.get_primitive(model)
                pipeline_without_preprocessor: Pipeline = self._generate_standard_pipeline(None, predictor)
                generated_pipelines[type_name].append(pipeline_without_preprocessor)

            # Generate all pipelines with preprocessors
            for p in preprocessors:
                preprocessor: PrimitiveBase = d3m_index.get_primitive(p)
                for model in model_list:
                    predictor: PrimitiveBase = d3m_index.get_primitive(model)

                    pipeline_with_preprocessor: Pipeline = self._generate_standard_pipeline(preprocessor, predictor)
                    generated_pipelines[type_name].append(pipeline_with_preprocessor)

        return generated_pipelines

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

    def generate_baseline_pipelines(self):
        """
        A wrapper function to generate a AutoSklearn pipeline
        TODO: should be deprecated and removed
        """
        raise Exception("This function is deprecated")
        autosklearn_pipeline = get_classification_pipeline(time_limit=60)
        # TODO: get other baseline primitives here
        return {"classification": [autosklearn_pipeline]}

    def output_automl_pipelines_to_mongodb(self):
        """
        Writes automl pipelines to mongo
        TODO: should be deprecated and removed
        """
        added_pipeline_sum = 0
        for pipeline_type in self.generated_pipelines:
            for pipe in self.generated_pipelines[pipeline_type]:
                added_pipeline_sum += self.mongo_database.add_to_automl_pipelines(pipe)

        logger.info("Results: {} pipelines added. {} pipelines already exist in database".format(added_pipeline_sum,
                                                                                           self.num_pipelines - added_pipeline_sum))

    def _wrap_generate_all_ensembles(self, k_ensembles: int = 3, p_preprocessors: int = 1) -> dict:
        """
        This function does differing preprocessors and same model, or differing models and same preprocessor
        It does NOT vary both.
        :param k_ensembles: Number of sub-pipelines
        :param p_preprocessors: Number of preprocessors per sub-pipeline
        :return: a dict containing the ensemble pipelines
        """
        all_ensembles = {"classification": [], "regression": []}
        preprocessor_combinations = list(combinations(self.preprocessors, p_preprocessors))

        logger.info("Starting different models, same preprocessor")

        # use K different models and the same preprocessor
        for problem_type in self.models:
            model_combinations = list(combinations(self.models[problem_type], k_ensembles))
            for model_list in model_combinations:
                for preprocessor in self.preprocessors:
                    generated = self.generate_k_ensembles(k_ensembles=k_ensembles, p_preprocessors=p_preprocessors,
                                                          given_preprocessors=[preprocessor], model=list(model_list),
                                                          same_model=True, same_preprocessor_order=True,
                                                          problem_type=problem_type)
                    all_ensembles[problem_type] += generated[problem_type]

        logger.info("Starting same models, different preprocessor")
        # use the same model and a all possible combinations of K preprocessors
        for problem_type in self.models:
            for model in self.models[problem_type]:
                for preprocessors in preprocessor_combinations:
                    generated = self.generate_k_ensembles(k_ensembles=k_ensembles, p_preprocessors=p_preprocessors,
                                                          given_preprocessors=preprocessors, model=model,
                                                          same_model=True, same_preprocessor_order=True,
                                                          problem_type=problem_type)
                    all_ensembles[problem_type] += generated[problem_type]


        return all_ensembles


    def generate_k_ensembles(self, k_ensembles: int, p_preprocessors, n_generated_pipelines: int = 1, model: str = None,
                             same_model: bool = True, same_preprocessor_order: bool = True,
                             problem_type: str = "classification", given_preprocessors: list = None) -> dict:
        """
        This function takes all the options on how to generate ensembles and then returns the created pipelines
        :param k_ensembles: the number of pipelines that will be ensembles together to form one big pipeline.
        :param p_preprocessors: the number of preprocessors before each predictor in each sub-pipeline.
        :param n_generated_pipelines: the number of pipelines to generate.
        :param model: the specific model to use in the task.  This can be a string or a list of strings.
        :param same_model: whether or not to use the same model every time as the predictor.
        :param same_preprocessor_order: Whether or not to use the same preprocessor order every time
        :param problem_type: whether to generate regression, classification, or both
        :param given_preprocessors: a list of given preprocessors that you want to use
        :return: a dictionary containing two keys "classification" and "regression" each containing the list of
        generated pipelines
        """

        if model is None and same_model:
            logger.info("Error: did not specify a model to ensemble with.  Please enter a valid model name.")
            raise Exception

        if k_ensembles == -1:
            k_ensembles = min(len(model), len(preprocessors))

        if problem_type == "all":
            problem_types = ["classification", "regression"]
        else:
            problem_types = [problem_type]

        # no point in generating the same pipeline twice (we were given a model and told to use the same order)
        if model is not None and same_preprocessor_order:
            n_generated_pipelines = 1

        # initialize values and constants
        generated_pipes = {'classification': [], 'regression': []}
        model_list = []
        preprocessor_list = []
        vertical_concat = d3m_index.get_primitive("d3m.primitives.data_transformation.horizontal_concat.DataFrameConcat")
        ensemble = d3m_index.get_primitive("d3m.primitives.classification.ensemble_voting.DSBOX")

        for algorithm_type in problem_types:
            # use the model given, or use random ones from all options
            if model is None:
                models_to_use = self.models[algorithm_type]
            else:
                models_to_use = model

            # Create the pipelines
            for _ in range(n_generated_pipelines):
                if same_model:
                    logger.info("Using the same model order")
                    # is there only one model? If so use it all the time
                    if type(models_to_use) == str or len(models_to_use) == 1:
                        if type(models_to_use) == list:
                            models_to_use = models_to_use[0]
                        # Generate k pipelines with different preprocessors and the same model
                        predictor: PrimitiveBase = d3m_index.get_primitive(models_to_use)
                        model_list = [predictor] * k_ensembles
                    else:
                        # use the models given in exactly that order
                        for index, algorithm in enumerate(models_to_use):
                            if index == k_ensembles:
                                break
                            predictor: PrimitiveBase = d3m_index.get_primitive(algorithm)
                            model_list.append(predictor)

                else:
                    logger.info("Randomly sampling models")
                    # Generate k pipelines with randomly sampled models
                    for index in range(len(models_to_use)):
                        algorithm = sample(models_to_use, 1)[0]
                        if index == k_ensembles:
                            break
                        predictor: PrimitiveBase = d3m_index.get_primitive(algorithm)
                        model_list.append(predictor)

                if same_preprocessor_order:
                    logger.info("Using the same preprocessor order")
                    # is there only one preprocessor? If so use it all the time
                    if given_preprocessors is not None:
                        if len(given_preprocessors) == 1:
                            logger.info("Only given one preprocessor")
                            preprocessor_to_use = given_preprocessors[0]
                            preprocessor: PrimitiveBase = d3m_index.get_primitive(preprocessor_to_use)
                            preprocessor_list = [[preprocessor] for x in range(k_ensembles)]
                        else:
                            logger.info("Only more than one preprocessor")
                            # there is more than one preprocessor given
                            for index, p in enumerate(given_preprocessors):
                                preprocessor: PrimitiveBase = d3m_index.get_primitive(p)
                                preprocessor_list.append([preprocessor])
                    else:
                        # this creates preprocessors with the same order every time
                        for index, p in enumerate(self.preprocessors):
                            if index == p_preprocessors:
                                break
                            preprocessor: PrimitiveBase = d3m_index.get_primitive(p)
                            preprocessor_list.append([preprocessor])

                else:
                    logger.info("Randomly sampling preprocessors")
                    # randomly sample preprocessors - til we have a new one for each model
                    for index in range(k_ensembles):
                        # get p preprocessor for each model
                        pre = sample(preprocessors, p_preprocessors)
                        if index == k_ensembles:
                            break
                        for p in pre:
                            preprocessor: PrimitiveBase = d3m_index.get_primitive(p)
                            preprocessor_list.append([preprocessor])
                logger.info(model_list)
                logger.info(preprocessor_list)
                final_pipeline = self.create_ensemble_pipeline(k_ensembles, p_preprocessors, preprocessor_list,
                                                               model_list, vertical_concat, ensemble)
                generated_pipes[algorithm_type].append(final_pipeline)

        return generated_pipes

    def create_ensemble_pipeline(self, k: int, p: int, preprocessor_list: List[str], model_list: List[str], concatenator: PrimitiveBase, 
                                 ensembler: PrimitiveBase) -> Pipeline:
        """
        This function does the nitty gritty work of preparing the pipeline and returning it
        :param k: the number of pipelines that will be ensembled
        :param p: the number of preprocessors for each sub-pipeline
        :param preprocessor_list: a list of preprocessors to use
        :param model_list:  the list of models to use
        :param concatenator: the primitive that will concantentate the pipelines
        :param ensembler: the ensembler that will ensemble all those pipelines together
        :return: the ensembled pipeline
        """

        logger.info("Creating {} pipelines of length {}".format(k, p+1))
        step_counter = 0

        # Creating Pipeline
        pipeline_description = EZPipeline(context=Context.TESTING)

        self._add_initial_steps(pipeline_description)
        list_of_outputs = []
        preprocessor_used = False

        # Add k pipelines
        for pipeline_number in range(k):
            # mod this in case we want repeats of the same model
            model = model_list[pipeline_number % len(model_list)]

            # Add Preprocessors Step
            for index, pre in enumerate(reversed(preprocessor_list[pipeline_number % len(preprocessor_list)])):
                if index == p:
                    break
                preprocessor_step = PrimitiveStep(primitive_description=pre.metadata.query())
                for arg in self._get_required_args(pre):
                    if arg == "outputs":
                        data_ref = pipeline_description.data_ref_of('target')
                    else:
                        data_ref = pipeline_description.data_ref_of('attrs')
                        preprocessor_used = True
                    preprocessor_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                        data_reference=data_ref)
                preprocessor_step.add_hyperparameter(name='use_semantic_types', argument_type=ArgumentType.VALUE, data=True)
                preprocessor_step.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="replace")
                preprocessor_step.add_output('produce')
                pipeline_description.add_step(preprocessor_step)

            # Classifier Step
            classifier_step = PrimitiveStep(primitive_description=model.metadata.query())
            for arg in self._get_required_args(model):
                # if no preprocessors make sure we are getting the data from the imputer
                if arg == "outputs":
                    data_ref = pipeline_description.data_ref_of('target')
                else:
                    if preprocessor_used:
                        data_ref = pipeline_description.curr_step_data_ref
                    else:
                        data_ref = pipeline_description.data_ref_of('attrs')
                classifier_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=data_ref)
            classifier_step.add_hyperparameter(name='use_semantic_types', argument_type=ArgumentType.VALUE, data=True)
            classifier_step.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="replace")
            classifier_step.add_hyperparameter(name='add_index_columns', argument_type=ArgumentType.VALUE, data=True)
            classifier_step.add_output('produce')
            pipeline_description.add_step(classifier_step)

            self._add_predictions_constructor(pipeline_description)
            list_of_outputs.append(pipeline_description.curr_step_data_ref)


        # concatenate k - 1 times
        for concat_num in range(k-1):
            if concat_num == 0:
                steps_data_ref_list = [list_of_outputs[concat_num], list_of_outputs[concat_num + 1]]
            else:
                steps_data_ref_list = [pipeline_description.curr_step_data_ref, list_of_outputs[concat_num + 1]]

            concat_step = PrimitiveStep(primitive_description=concatenator.metadata.query())
            for arg_index, arg in enumerate(self._get_required_args(concatenator)):
                concat_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=steps_data_ref_list[arg_index])
            concat_step.add_output('produce')
            pipeline_description.add_step(concat_step)


        # finally ensemble them all together
        renamer = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.rename_duplicate_name.DataFrameCommon'))
        for arg_index, arg in enumerate(self._get_required_args(ensembler)):
            renamer.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                data_reference=pipeline_description.curr_step_data_ref)
        renamer.add_output('produce')
        pipeline_description.add_step(renamer)

        # finally ensemble them all together TODO: change the RF to be dynamic
        ensemble_model = d3m_index.get_primitive('d3m.primitives.regression.random_forest.SKlearn')
        ensemble_step = PrimitiveStep(primitive_description=ensemble_model.metadata.query())
        for arg_index, arg in enumerate(self._get_required_args(ensemble_model)):
            if arg == "outputs":
                ensemble_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=pipeline_description.data_ref_of('target'))
            else:
                ensemble_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=pipeline_description.curr_step_data_ref)
        ensemble_step.add_output('produce')
        pipeline_description.add_step(ensemble_step)

        # output them as predictions
        self._add_predictions_constructor(pipeline_description)

        # Adding output step to the pipeline
        pipeline_description.add_output(name='Output', data_reference=pipeline_description.curr_step_data_ref)

        return pipeline_description



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

    def generate_metafeatures_pipeline(self) -> dict:
        """
        Generates the standard metafeature pipeline
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

        # column_parser step
        add_pipeline_step(
            pipeline_description,
            'd3m.primitives.data_transformation.column_parser.DataFrameCommon'
        )

        # metafeature_extractor step
        add_pipeline_step(
            pipeline_description,
            'd3m.primitives.metalearning.metafeature_extractor.BYU'
        )

        pipeline_description.add_output(name='output predictions', data_reference=pipeline_description.curr_step_data_ref)

        with open("metafeature_extractor_pipeline.json", "w") as file:
            json.dump(pipeline_description.to_json_structure(), file, indent=2, default=json_util.default)

        return {"classification": [pipeline_description], "regression": [pipeline_description]}


def _pretty_print_json(self, json_obj: str):
    """
    Pretty prints a JSON object to make it readable
    """
    import pprint
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(json_obj)
