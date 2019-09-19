import sys
import unittest

from d3m.metadata.base import Context, ArgumentType

from experimenter.pipeline_builder import EZPipeline, create_pipeline_step, add_pipeline_step


class PipelineGenerationTestCase(unittest.TestCase):

    # Test methods
    
    def test_curr_step_i(self) -> None:
        pipeline = self._make_no_steps_pipeline()

        # current step index should start as `None`
        # when there are no steps
        self.assertEqual(pipeline.curr_step_i, None)

        self._add_dataset_to_df_step(pipeline)
        self.assertEqual(pipeline.curr_step_i, 0)

        self._add_column_parser_step(pipeline)
        self.assertEqual(pipeline.curr_step_i, 1)
    
    def test_refs(self) -> None:
        pipeline = self._make_no_steps_pipeline()

        self._add_dataset_to_df_step(pipeline)
        pipeline.set_step_i_of('raw_df')
        self.assertEqual(pipeline.data_ref_of('raw_df'), 'steps.0.produce')

        self._add_column_parser_step(pipeline)
        self.assertEqual(pipeline.curr_step_data_ref, 'steps.1.produce')

        self._add_extract_attrs_step(pipeline)
        pipeline.set_step_i_of('attrs')
        self.assertEqual(pipeline.data_ref_of('attrs'), 'steps.2.produce')

        # setting a different ref should not affect an already set ref
        self.assertEqual(pipeline.data_ref_of('raw_df'), 'steps.0.produce')

        # invalid ref names should be invalid
        with self.assertRaises(Exception):
            pipeline.set_step_i_of('Jar Jar Binks')
        with self.assertRaises(Exception):
            pipeline.data_ref_of('Han Solo')
        
    # Private methods

    def _make_no_steps_pipeline(self) -> EZPipeline:
        pipeline = EZPipeline(context=Context.TESTING)
        pipeline.add_input(name='inputs')
        return pipeline

    def _add_dataset_to_df_step(self, pipeline: EZPipeline) -> None:
        add_pipeline_step(
            pipeline,
            'd3m.primitives.data_transformation.dataset_to_dataframe.Common',
            'inputs.0'
        )

    def _add_column_parser_step(self, pipeline: EZPipeline) -> None:
        add_pipeline_step(
            pipeline,
            'd3m.primitives.data_transformation.column_parser.DataFrameCommon'
        )
    
    def _add_extract_attrs_step(self, pipeline: EZPipeline) -> None:
        extract_attributes_step = create_pipeline_step(
            'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon',
            pipeline.curr_step_data_ref
        )
        extract_attributes_step.add_hyperparameter(name='semantic_types', argument_type=ArgumentType.VALUE,
                                  data=['https://metadata.datadrivendiscovery.org/types/Attribute'])
        pipeline.add_step(extract_attributes_step)
