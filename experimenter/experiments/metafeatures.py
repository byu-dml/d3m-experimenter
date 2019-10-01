from typing import Dict, List
import json

from d3m.metadata.pipeline import Pipeline
from d3m.metadata.base import Context
from bson import json_util

from experimenter.experiments.experiment import Experiment
from experimenter.pipeline_builder import EZPipeline, PipelineArchDesc, add_pipeline_step

class MetafeatureExperimenter(Experiment):
    """
    Builds pipelines that will compute the metafeatures of
    a dataset.
    """

    def generate_pipelines(self) -> Dict[str, List[Pipeline]]:
        pipeline_description = self.generate_pipeline()
        return {"classification": [pipeline_description], "regression": [pipeline_description]}
    
    def generate_pipeline(self) -> Pipeline:
        """
        Generates the standard metafeature pipeline
        """
        # Creating pipeline
        architecture = PipelineArchDesc("metafeatures")
        pipeline_description = EZPipeline(arch_desc=architecture, context=Context.TESTING)
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
        
        return pipeline_description