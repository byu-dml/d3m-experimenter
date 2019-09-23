from typing import Dict, List

from d3m.metadata.pipeline import Pipeline, PrimitiveStep
from d3m.primitive_interfaces.base import PrimitiveBase
from d3m import index as d3m_index
from d3m.metadata.base import Context, ArgumentType

from experimenter.constants import EXTRA_HYPEREPARAMETERS

from experimenter.experiments.experiment import Experiment
from experimenter.pipeline_builder import EZPipeline, add_initial_steps, get_required_args, add_predictions_constructor

class StraightArchitectureExperimenter(Experiment):
    """
    Generates diverse pipelines of straight architectures.
    """

    def generate_pipelines(
        self,
        preprocessors: List[str],
        models: Dict[str,str]
    ) -> Dict[str, List[Pipeline]]:
        """
        A high level function to create numerous pipelines for a list of preprocessor and model
        :param preprocessors: a list of preprocessors to generate pipelines with
        :param models: a dict containing two keys of `classification` and `regression` each with a list of model primitive names
        :return: a dict containing two keys of `classification` and `regression` each a list of pipeline objects
        """
        preprocessors = list(set(preprocessors))

        generated_pipelines = {"classification": [], "regression": []}
        for type_name, model_list in models.items():
            # Generate all pipelines without preprocessors
            for model in model_list:
                predictor: PrimitiveBase = d3m_index.get_primitive(model)
                pipeline_without_preprocessor: Pipeline = self.generate_pipeline(None, predictor)
                generated_pipelines[type_name].append(pipeline_without_preprocessor)

            # Generate all pipelines with preprocessors
            for p in preprocessors:
                preprocessor: PrimitiveBase = d3m_index.get_primitive(p)
                for model in model_list:
                    predictor: PrimitiveBase = d3m_index.get_primitive(model)

                    pipeline_with_preprocessor: Pipeline = self.generate_pipeline(preprocessor, predictor)
                    generated_pipelines[type_name].append(pipeline_with_preprocessor)

        return generated_pipelines

    def generate_pipeline(self, preprocessor: PrimitiveBase, classifier: PrimitiveBase) -> Pipeline:
        """
        Adds the crucial preprocess or classifier steps to a basic pipeline description and returns the pipeline
        :param preprocessor: the primitive to use as a preprocessor
        :param classifier: the primitive to use as a classifier
        :return a newly created pipeline
        """

        # Creating Pipeline
        pipeline_description = EZPipeline(context=Context.TESTING)

        add_initial_steps(pipeline_description)
        preprocessor_used = False

        # Preprocessor Step
        if preprocessor:
            preprocessor_step = PrimitiveStep(primitive_description=preprocessor.metadata.query())
            for arg in get_required_args(preprocessor):
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
        for arg in get_required_args(classifier):
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
        # handle any extra hyperparams needed
        if classifier in EXTRA_HYPEREPARAMETERS:
            params = EXTRA_HYPEREPARAMETERS[classifier]
            classifier_step.add_hyperparameter(name=params["name"], argument_type=params["type"], data=params["data"])
        classifier_step.add_output('produce')
        pipeline_description.add_step(classifier_step)

        add_predictions_constructor(pipeline_description)

        # Adding output step to the pipeline
        pipeline_description.add_output(name='Output', data_reference=pipeline_description.curr_step_data_ref)

        return pipeline_description
