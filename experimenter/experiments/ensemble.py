import logging
logger = logging.getLogger(__name__)
from typing import Dict, List
from itertools import combinations
from random import sample

from d3m.metadata.pipeline import Pipeline, PrimitiveStep
from d3m.primitive_interfaces.base import PrimitiveBase
from d3m.metadata.base import Context, ArgumentType
from d3m import index as d3m_index

from experimenter.experiments.experiment import Experiment
from experimenter.pipeline_builder import EZPipeline, map_pipeline_step_arguments, add_initial_steps, get_required_args, add_predictions_constructor

class EnsembleArchitectureExperimenter(Experiment):
    """
    Generates diverse pipelines with ensemble architectures.
    """

    def generate_pipelines(
        self,
        preprocessors: list,
        models: Dict[str,str],
        n_classifiers: int,
        n_preprocessors: int
    ) -> Dict[str, List[Pipeline]]:
        """
        This function does differing preprocessors and same model, or differing models and same preprocessor
        It does NOT vary both.
        :param preprocessors: List all of preprocessors that are available to use.
        :param models: dictionary of all models that are available to use.
        :param n_classifiers: Used to determine the number of sub-pipelines
        :param n_preprocessors: Number of preprocessors per sub-pipeline
        :return: a dict containing the ensemble pipelines
        """
        all_ensembles = {"classification": [], "regression": []}
        preprocessor_combinations = list(combinations(preprocessors, n_preprocessors))

        logger.info("Starting different models, same preprocessor")

        # use K different models and the same preprocessor
        for problem_type in models:
            model_combinations = list(combinations(models[problem_type], n_classifiers))
            for model_list in model_combinations:
                for preprocessor in preprocessors:
                    generated = self._generate_k_ensembles(k_ensembles=n_classifiers, n_preprocessors=n_preprocessors,
                                                          preprocessors=preprocessors, models=models,
                                                          given_preprocessors=[preprocessor], model=list(model_list),
                                                          same_model=True, same_preprocessor_order=True,
                                                          problem_type=problem_type)
                    all_ensembles[problem_type] += generated[problem_type]

        logger.info("Starting same models, different preprocessor")
        # use the same model and a all possible combinations of K preprocessors
        for problem_type in models:
            for model in models[problem_type]:
                for preprocessors in preprocessor_combinations:
                    generated = self._generate_k_ensembles(k_ensembles=n_classifiers, n_preprocessors=n_preprocessors,
                                                          preprocessors=preprocessors, models=models,
                                                          given_preprocessors=preprocessors, model=model,
                                                          same_model=True, same_preprocessor_order=True,
                                                          problem_type=problem_type)
                    all_ensembles[problem_type] += generated[problem_type]


        return all_ensembles

    def generate_pipeline(self, k: int, p: int, preprocessor_list: List[str], model_list: List[str], concatenator: PrimitiveBase, 
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

        # Creating Pipeline
        pipeline_description = EZPipeline(context=Context.TESTING)

        add_initial_steps(pipeline_description)
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
                req_args = get_required_args(pre)
                for arg in req_args:
                    if arg != "outputs":
                        preprocessor_used = True
                        break
                map_pipeline_step_arguments(
                    pipeline_description,
                    preprocessor_step,
                    req_args
                )
                pipeline_description.add_step(preprocessor_step)

            # Classifier Step
            classifier_step = PrimitiveStep(primitive_description=model.metadata.query())
            map_pipeline_step_arguments(
                pipeline_description,
                classifier_step,
                get_required_args(model),
                preprocessor_used
            )
            classifier_step.add_hyperparameter(name='add_index_columns', argument_type=ArgumentType.VALUE, data=True)
            pipeline_description.add_step(classifier_step)

            add_predictions_constructor(pipeline_description)
            list_of_outputs.append(pipeline_description.curr_step_data_ref)


        # concatenate k - 1 times
        for concat_num in range(k-1):
            if concat_num == 0:
                steps_data_ref_list = [list_of_outputs[concat_num], list_of_outputs[concat_num + 1]]
            else:
                steps_data_ref_list = [pipeline_description.curr_step_data_ref, list_of_outputs[concat_num + 1]]

            concat_step = PrimitiveStep(primitive_description=concatenator.metadata.query())
            for arg_index, arg in enumerate(get_required_args(concatenator)):
                concat_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=steps_data_ref_list[arg_index])
            concat_step.add_output('produce')
            pipeline_description.add_step(concat_step)


        # finally ensemble them all together
        renamer = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.rename_duplicate_name.DataFrameCommon'))
        for arg_index, arg in enumerate(get_required_args(ensembler)):
            renamer.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                data_reference=pipeline_description.curr_step_data_ref)
        renamer.add_output('produce')
        pipeline_description.add_step(renamer)

        # finally ensemble them all together TODO: change the RF to be dynamic
        ensemble_model = d3m_index.get_primitive('d3m.primitives.regression.random_forest.SKlearn')
        ensemble_step = PrimitiveStep(primitive_description=ensemble_model.metadata.query())
        for arg_index, arg in enumerate(get_required_args(ensemble_model)):
            if arg == "outputs":
                ensemble_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=pipeline_description.data_ref_of('target'))
            else:
                ensemble_step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                                    data_reference=pipeline_description.curr_step_data_ref)
        ensemble_step.add_output('produce')
        pipeline_description.add_step(ensemble_step)

        # output them as predictions
        add_predictions_constructor(pipeline_description)

        # Adding output step to the pipeline
        pipeline_description.add_output(name='Output', data_reference=pipeline_description.curr_step_data_ref)

        return pipeline_description

    def _generate_k_ensembles(self, k_ensembles: int, n_preprocessors, preprocessors: list, models: dict,
                             n_generated_pipelines: int = 1, model: str = None, same_model: bool = True,
                             same_preprocessor_order: bool = True, problem_type: str = "classification",
                             given_preprocessors: list = None) -> dict:
        """
        This function takes all the options on how to generate ensembles and then returns the created pipelines
        :param k_ensembles: the number of pipelines that will be ensembles together to form one big pipeline.
        :param n_preprocessors: the number of preprocessors before each predictor in each sub-pipeline.
        :param preprocessors: List all of preprocessors that are available to use.
        :param models: dictionary of all models that are available to use.
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
                models_to_use = models[algorithm_type]
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
                        for index, p in enumerate(preprocessors):
                            if index == n_preprocessors:
                                break
                            preprocessor: PrimitiveBase = d3m_index.get_primitive(p)
                            preprocessor_list.append([preprocessor])

                else:
                    logger.info("Randomly sampling preprocessors")
                    # randomly sample preprocessors - til we have a new one for each model
                    for index in range(k_ensembles):
                        # get p preprocessor for each model
                        pre = sample(preprocessors, n_preprocessors)
                        if index == k_ensembles:
                            break
                        for p in pre:
                            preprocessor: PrimitiveBase = d3m_index.get_primitive(p)
                            preprocessor_list.append([preprocessor])
                logger.info(model_list)
                logger.info(preprocessor_list)
                final_pipeline = self.generate_pipeline(k_ensembles, n_preprocessors, preprocessor_list,
                                                               model_list, vertical_concat, ensemble)
                generated_pipes[algorithm_type].append(final_pipeline)

        return generated_pipes
