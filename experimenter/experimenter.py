from random import sample

from .constants import models, preprocessors, problem_directories, blacklist_non_tabular_data
from d3m import index as d3m_index
from d3m import utils as d3m_utils
from d3m.primitive_interfaces.base import PrimitiveBase
from d3m.metadata.pipeline import PrimitiveStep
from d3m.metadata.base import Context, ArgumentType
from typing import List
import logging
from d3m.metadata.pipeline import Pipeline
import os
import json
from .database_communication import PipelineDB
from itertools import combinations
from bson import json_util
from d3m.metadata import base as metadata_base, problem as base_problem
from experimenter.autosklearn.pipelines import get_classification_pipeline, AutoSklearnClassifierPrimitive

from experimenter import utils

logger = logging.getLogger(__name__)


def register_primitives():
    with d3m_utils.silence():
        d3m_index.register_primitive(
            AutoSklearnClassifierPrimitive.metadata.query()['python_path'],
            AutoSklearnClassifierPrimitive
        )

class Experimenter:
    """
    This class is initialized with all the paths info needed to find and create pipelines.
    It first finds all possible problems in the datasets_dir/problem_directories/* and then
    generates pipelines.  This class is used by the ExperimenterDriver class to run the pipelines.
    @:param input_models: a dictionary of two items, "classification" and "regression", each a list of primitive machine
    learning models
    """

    def __init__(self, datasets_dir: str, volumes_dir: str, input_problem_directory=None,
                 input_models=None, input_preprocessors=None, generate_pipelines=True,
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
            print("Generating problems...")
            self.problems = self.get_possible_problems()
            self.num_problems = len(self.problems["classification"]) + len(self.problems["regression"])

            print("There are {} problems".format(self.num_problems))

        if generate_pipelines:
            print("Generating pipelines...")
            # self.generated_pipelines: dict = self.generate_pipelines(self.preprocessors, self.models)
            pipeline = self.generate_metafeatures_pipeline()
            # TODO: create a system for how to use the next line
            self.generated_pipelines: dict = self._wrap_generate_all_ensembles()
            # self.generated_pipelines: dict = self.generate_k_ensembles(k_ensembles=3, p_preprocessors=0,
            #                                                            n_generated_pipelines=50, same_model=False,
            #                                                            same_preprocessor_order=False, problem_type="all")
            self.num_pipelines = len(self.generated_pipelines["classification"]) + \
                                 len(self.generated_pipelines["regression"])

            print("There are {} pipelines".format(self.num_pipelines))

            if location is None:
                self.mongo_database = PipelineDB()
                print('Exporting pipelines to mongodb...')
                self.output_pipelines_to_mongodb()
            elif location == "test":
                pass
            else:
                print("Exporting pipelines to {}".format(location))
                self.output_values_to_folder(location)

        if generate_automl_pipelines:
            self.generated_pipelines = self.generate_baseline_pipelines()
            self.num_pipelines = len(self.generated_pipelines["classification"])
            self.output_automl_pipelines_to_mongodb()


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
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.dataset_to_dataframe.Common'))
        step_1.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='inputs.0')
        step_1.add_output('produce')
        pipeline_description.add_step(step_1)
        step_counter += 1

        # Step 2: column_parser
        step_2 = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.column_parser.DataFrameCommon'))
        step_2.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER,
                            data_reference='steps.{}.produce'.format(step_counter - 1))
        step_2.add_output('produce')
        pipeline_description.add_step(step_2)
        step_counter += 1

        # Step 3: Imputer
        sk_imputer: PrimitiveBase = d3m_index.get_primitive("d3m.primitives.data_preprocessing.random_sampling_imputer.BYU")
        step_3 = PrimitiveStep(primitive_description=sk_imputer.metadata.query())
        step_3.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER,
                            data_reference = 'steps.{}.produce'.format(step_counter - 1))
        step_3.add_output('produce')
        pipeline_description.add_step(step_3)
        step_counter += 1

        # Step 4: extract_columns_by_semantic_types(targets)
        step_4 = PrimitiveStep(primitive=d3m_index.get_primitive(
            'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon'))
        step_4.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='steps.0.produce')
        step_4.add_output('produce')
        step_4.add_hyperparameter(name='semantic_types', argument_type=ArgumentType.VALUE,
                                  data=['https://metadata.datadrivendiscovery.org/types/TrueTarget'])
        pipeline_description.add_step(step_4)
        step_counter += 1

        return step_counter

    def _add_predictions_constructor(self, pipeline_description, step_counter):
        # Step 6: PredictionsConstructor
        predictions_constructor: PrimitiveBase = d3m_index.get_primitive("d3m.primitives.data_transformation.construct_predictions.DataFrameCommon")
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
        preprocessor_used = False

        # Step 4: Preprocessor
        if preprocessor:
            step_4 = PrimitiveStep(primitive_description=preprocessor.metadata.query())
            for arg in self._get_required_args(preprocessor):
                if arg == "outputs":
                    data_ref = 'steps.3.produce'
                else:
                    data_ref = 'steps.{}.produce'.format(step_counter - 2)
                    preprocessor_used = True

                step_4.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=data_ref)
            step_4.add_hyperparameter(name='use_semantic_types', argument_type=ArgumentType.VALUE, data=True)
            step_4.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="replace")
            step_4.add_output('produce')
            pipeline_description.add_step(step_4)
            step_counter += 1

        # Step 5: Classifier
        step_5 = PrimitiveStep(primitive_description=classifier.metadata.query())
        for index, arg in enumerate(self._get_required_args(classifier)):
            if arg == "outputs":
                data_ref = 'steps.3.produce'
            else:
                # if we haven't used a preprocessor, we have to go back two to get the full dataframe
                bias = 0 if preprocessor_used else -1
                data_ref = 'steps.{}.produce'.format(step_counter - 1 + bias)
            step_5.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                data_reference=data_ref)
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

    def generate_baseline_pipelines(self):
        register_primitives()
        autosklearn_pipeline = get_classification_pipeline(time_limit=60)
        # TODO: get other baseline primitives here
        return {"classification": [autosklearn_pipeline]}

    def output_automl_pipelines_to_mongodb(self):
        added_pipeline_sum = 0
        for pipeline_type in self.generated_pipelines:
            for pipe in self.generated_pipelines[pipeline_type]:
                added_pipeline_sum += self.mongo_database.add_to_automl_pipelines(pipe)

        print("Results: {} pipelines added. {} pipelines already exist in database".format(added_pipeline_sum,
                                                                                           self.num_pipelines - added_pipeline_sum))

    def _wrap_generate_all_ensembles(self, k_ensembles=3, p_preprocessors=1):
        """
        This function does differing preprocessors and same model, or differing models and same preprocessor
        It does NOT vary both.
        :param k_ensembles: Number of sub-pipelines
        :param p_preprocessors: Number of preprocessors per sub-pipeline
        :return: a dict containing the ensemble pipelines
        """
        all_ensembles = {"classification": [], "regression": []}
        preprocessor_combinations = list(combinations(self.preprocessors, k_ensembles))


        print("Starting different models, same preprocessor")

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

        print("Starting same models, different preprocessor")
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


    def generate_k_ensembles(self, k_ensembles: int, p_preprocessors, n_generated_pipelines: int = 1, model=None,
                             same_model: bool = True, same_preprocessor_order: bool = True,
                             problem_type="classification", given_preprocessors: list = None):
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
            print("Error: did not specify a model to ensemble with.  Please enter a valid model name.")
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
        ensemble = d3m_index.get_primitive("d3m.primitives.data_preprocessing.EnsembleVoting.DSBOX")

        for algorithm_type in problem_types:
            # use the model given, or use random ones from all options
            if model is None:
                models_to_use = self.models[algorithm_type]
            else:
                models_to_use = model

            # Create the pipelines
            for _ in range(n_generated_pipelines):
                if same_model:
                    print("Using the same model order")
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
                    print("Randomly sampling models")
                    # Generate k pipelines with randomly sampled models
                    for index in range(len(models_to_use)):
                        algorithm = sample(models_to_use, 1)[0]
                        if index == k_ensembles:
                            break
                        predictor: PrimitiveBase = d3m_index.get_primitive(algorithm)
                        model_list.append(predictor)

                if same_preprocessor_order:
                    print("Using the same preprocessor order")
                    # is there only one preprocessor? If so use it all the time
                    if given_preprocessors is not None:
                        if len(given_preprocessors) == 1:
                            print("Only given one preprocessor")
                            preprocessor_to_use = given_preprocessors[0]
                            preprocessor: PrimitiveBase = d3m_index.get_primitive(preprocessor_to_use)
                            preprocessor_list = [[preprocessor] for x in range(k_ensembles)]
                        else:
                            print("Only more than one preprocessor")
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
                    print("Randomly sampling preprocessors")
                    # randomly sample preprocessors - til we have a new one for each model
                    for index in range(k_ensembles):
                        # get p preprocessor for each model
                        pre = sample(preprocessors, p_preprocessors)
                        if index == k_ensembles:
                            break
                        for p in pre:
                            preprocessor: PrimitiveBase = d3m_index.get_primitive(p)
                            preprocessor_list.append([preprocessor])
                print(model_list)
                print(preprocessor_list)
                final_pipeline = self.create_ensemble_pipeline(k_ensembles, p_preprocessors, preprocessor_list,
                                                               model_list, vertical_concat, ensemble)
                generated_pipes[algorithm_type].append(final_pipeline)

        return generated_pipes

    def create_ensemble_pipeline(self, k, p, preprocessor_list, model_list, concatenator, ensembler):
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

        print("Creating {} pipelines of length {}".format(k, p+1))
        step_counter = 0

        # Creating Pipeline
        pipeline_description = Pipeline(context=Context.TESTING)
        pipeline_description.add_input(name='inputs')

        step_counter = self._add_initial_steps(pipeline_description, step_counter)
        init_step_counter = step_counter
        list_of_outputs = []
        preprocessor_used = False

        # Add k pipelines
        for pipeline_number in range(k):
            # mod this in case we want repeats of the same model
            model = model_list[pipeline_number % len(model_list)]

            # Step 4: Add P Pre=processors
            for index, pre in enumerate(reversed(preprocessor_list[pipeline_number % len(preprocessor_list)])):
                if index == p:
                    break
                step_4 = PrimitiveStep(primitive_description=pre.metadata.query())
                for arg in self._get_required_args(pre):
                    if arg == "outputs":
                        data_ref = 'steps.3.produce'
                    else:
                        data_ref = 'steps.{}.produce'.format(init_step_counter - 2)
                        preprocessor_used = True
                    step_4.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                        data_reference=data_ref)
                step_4.add_hyperparameter(name='use_semantic_types', argument_type=ArgumentType.VALUE, data=True)
                step_4.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="replace")
                step_4.add_output('produce')
                pipeline_description.add_step(step_4)
                step_counter += 1

            # Step 5: Classifier
            step_5 = PrimitiveStep(primitive_description=model.metadata.query())
            for arg in self._get_required_args(model):
                # if no preprocessors make sure we are getting the data from the imputer
                if not preprocessor_used:
                    data_ref = 'steps.{}.produce'.format(init_step_counter - 2)
                else:
                    data_ref = 'steps.{}.produce'.format(step_counter - 1)

                step_5.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=data_ref)
            step_5.add_hyperparameter(name='use_semantic_types', argument_type=ArgumentType.VALUE, data=True)
            step_5.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="replace")
            step_5.add_output('produce')
            pipeline_description.add_step(step_5)
            step_counter += 1

            step_counter = self._add_predictions_constructor(pipeline_description, step_counter)
            list_of_outputs.append(step_counter - 1)


        # concatenate k - 1 times
        for concat_num in range(k-1):
            if concat_num == 0:
                steps_list = [list_of_outputs[concat_num], list_of_outputs[concat_num + 1]]
            else:
                steps_list = [step_counter - 1, list_of_outputs[concat_num + 1]]

            step_6 = PrimitiveStep(primitive_description=concatenator.metadata.query())
            for arg_index, arg in enumerate(self._get_required_args(concatenator)):
                step_6.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference='steps.{}.produce'.format(steps_list[arg_index]))
            step_6.add_output('produce')
            pipeline_description.add_step(step_6)
            step_counter += 1


        # finally ensemble them all together
        renamer = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.rename_duplicate_name.DataFrameCommon'))
        for arg_index, arg in enumerate(self._get_required_args(ensembler)):
            renamer.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                data_reference='steps.{}.produce'.format(step_counter - 1))
        renamer.add_output('produce')
        pipeline_description.add_step(renamer)
        step_counter += 1

        # finally ensemble them all together
        step_8 = PrimitiveStep(primitive_description=ensembler.metadata.query())
        for arg_index, arg in enumerate(self._get_required_args(ensembler)):
            step_8.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                data_reference='steps.{}.produce'.format(step_counter - 1))
        step_8.add_output('produce')
        pipeline_description.add_step(step_8)
        step_counter += 1

        # output them as predictions
        step_counter = self._add_predictions_constructor(pipeline_description, step_counter)

        # Adding output step to the pipeline
        pipeline_description.add_output(name='Output', data_reference='steps.{}.produce'.format(step_counter - 1))

        return pipeline_description



    def generate_default_pipeline(self):
        """
        Example from https://docs.datadrivendiscovery.org/devel/pipeline.html#pipeline-description-example
        :return: the sample pipeline
        """
        # Creating pipeline
        pipeline_description = Pipeline(context=Context.TESTING)
        pipeline_description.add_input(name='inputs')

        # Step 1: dataset_to_dataframe
        step_0 = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.dataset_to_dataframe.Common'))
        step_0.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='inputs.0')
        step_0.add_output('produce')
        pipeline_description.add_step(step_0)

        # Step 2: column_parser
        step_1 = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.column_parser.DataFrameCommon'))
        step_1.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='steps.0.produce')
        step_1.add_output('produce')
        pipeline_description.add_step(step_1)

        # Step 3: extract_columns_by_semantic_types(attributes)
        step_2 = PrimitiveStep(primitive=d3m_index.get_primitive(
            'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon'))
        step_2.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='steps.1.produce')
        step_2.add_output('produce')
        step_2.add_hyperparameter(name='semantic_types', argument_type=ArgumentType.VALUE,
                                  data=['https://metadata.datadrivendiscovery.org/types/Attribute'])
        pipeline_description.add_step(step_2)

        # Step 4: extract_columns_by_semantic_types(targets)
        step_3 = PrimitiveStep(primitive=d3m_index.get_primitive(
            'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon'))
        step_3.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='steps.0.produce')
        step_3.add_output('produce')
        step_3.add_hyperparameter(name='semantic_types', argument_type=ArgumentType.VALUE,
                                  data=['https://metadata.datadrivendiscovery.org/types/TrueTarget'])
        pipeline_description.add_step(step_3)

        attributes = 'steps.2.produce'
        targets = 'steps.3.produce'

        # Step 5: imputer
        step_4 = PrimitiveStep(primitive=d3m_index.get_primitive('d3m.primitives.data_cleaning.imputer.SKlearn'))
        step_4.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference=attributes)
        step_4.add_output('produce')
        pipeline_description.add_step(step_4)

        # Step 6: random_forest
        step_5 = PrimitiveStep(primitive=d3m_index.get_primitive('d3m.primitives.regression.random_forest.SKlearn'))
        step_5.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='steps.4.produce')
        step_5.add_argument(name='outputs', argument_type=ArgumentType.CONTAINER, data_reference=targets)
        step_5.add_output('produce')
        pipeline_description.add_step(step_5)

        # Final Output
        pipeline_description.add_output(name='output predictions', data_reference='steps.5.produce')

        # Output to YAML
        return {"classification": [pipeline_description], "regression": []}

    def generate_metafeatures_pipeline(self):
        # Creating pipeline
        pipeline_description = Pipeline(context=Context.TESTING)
        pipeline_description.add_input(name='inputs')

        # Step 1: dataset_to_dataframe
        step_0 = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.dataset_to_dataframe.Common'))
        step_0.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='inputs.0')
        step_0.add_output('produce')
        pipeline_description.add_step(step_0)

        # Step 2: column_parser
        step_1 = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.column_parser.DataFrameCommon'))
        step_1.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='steps.0.produce')
        step_1.add_output('produce')
        pipeline_description.add_step(step_1)

        # Step 2: column_parser
        step_2 = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.metafeature_extraction.metafeature_extractor.BYU'))
        step_2.add_argument(name='inputs', argument_type=ArgumentType.CONTAINER, data_reference='steps.1.produce')
        step_2.add_output('produce')
        pipeline_description.add_step(step_2)

        pipeline_description.add_output(name='output predictions', data_reference='steps.2.produce')

        with open("metafeature_extractor_pipeline.json", "w") as file:
            json.dump(pipeline_description.to_json_structure(), file, indent=2, default=json_util.default)

        return {"classification": [pipeline_description], "regression": [pipeline_description]}, 1
