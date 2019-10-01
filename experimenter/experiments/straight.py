from typing import Dict, List

from d3m.metadata.pipeline import Pipeline, PrimitiveStep
from d3m.primitive_interfaces.base import PrimitiveBase
from d3m import index as d3m_index
from d3m.metadata.base import Context, ArgumentType

from experimenter.experiments.experiment import Experiment
from experimenter.pipeline_builder import (
    EZPipeline, PipelineArchDesc, map_pipeline_step_arguments, add_initial_steps, get_required_args, add_predictions_constructor
)

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
        architecture = PipelineArchDesc("straight")
        pipeline_description = EZPipeline(arch_desc=architecture, context=Context.TESTING)

        add_initial_steps(pipeline_description)
        preprocessor_used = False

        # Preprocessor Step
        if preprocessor:
            preprocessor_step = PrimitiveStep(primitive_description=preprocessor.metadata.query())
            req_args = get_required_args(preprocessor)
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
        
        pipeline_description.arch_desc.generation_parameters["preprocessor_used"] = preprocessor_used

        # Classifier Step
        classifier_step = PrimitiveStep(primitive_description=classifier.metadata.query())
        map_pipeline_step_arguments(
            pipeline_description,
            classifier_step,
            get_required_args(classifier),
            preprocessor_used
        )
        pipeline_description.add_step(classifier_step)

        add_predictions_constructor(pipeline_description)

        # Adding output step to the pipeline
        pipeline_description.add_output(name='Output', data_reference=pipeline_description.curr_step_data_ref)

        return pipeline_description
