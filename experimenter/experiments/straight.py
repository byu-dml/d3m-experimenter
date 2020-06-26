from typing import Dict, List

from d3m.metadata.pipeline import Pipeline, PrimitiveStep
from d3m.primitive_interfaces.base import PrimitiveBase
from d3m.metadata.base import Context, ArgumentType

from experimenter.experiments.experiment import Experiment
from experimenter.pipeline_builder import EZPipeline, PipelineArchDesc
from experimenter.config import d3m_index


class StraightArchitectureExperimenter(Experiment):
    """
    Generates diverse pipelines of straight architectures.
    """

    def generate_pipelines(
        self, *, preprocessors: List[str], models: Dict[str, str], **unused_args
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
                pipeline_without_preprocessor: Pipeline = self.generate_pipeline(
                    None, model
                )
                generated_pipelines[type_name].append(pipeline_without_preprocessor)

            # Generate all pipelines with preprocessors
            for p in preprocessors:
                for model in model_list:
                    pipeline_with_preprocessor: Pipeline = self.generate_pipeline(
                        p, model
                    )
                    generated_pipelines[type_name].append(pipeline_with_preprocessor)

        return generated_pipelines

    def generate_pipeline(self, preprocessor: str, classifier: str) -> Pipeline:
        """
        Adds the crucial preprocess or classifier steps to a basic pipeline description and returns the pipeline
        :param preprocessor: the python path of the primitive to use as a preprocessor
        :param classifier: the python path of the primitive to use as a classifier
        :return a newly created pipeline
        """

        # Creating Pipeline
        architecture = PipelineArchDesc("straight")
        pipeline_description = EZPipeline(
            arch_desc=architecture, add_preparation_steps=True, context=Context.TESTING
        )

        preprocessor_used = False

        # Preprocessor Step
        if preprocessor:
            pipeline_description.add_primitive_step(
                preprocessor, pipeline_description.data_ref_of("attrs")
            )
            preprocessor_used = True

        pipeline_description.arch_desc.generation_parameters[
            "preprocessor_used"
        ] = preprocessor_used

        # Classifier Step

        # We want to use the preprocessor's results as input to the classifier
        # if we used a preprocessor.
        if preprocessor_used:
            model_args_data_ref = pipeline_description.curr_step_data_ref
        else:
            model_args_data_ref = pipeline_description.data_ref_of("attrs")

        pipeline_description.add_primitive_step(classifier, model_args_data_ref)

        pipeline_description.finalize()

        return pipeline_description
