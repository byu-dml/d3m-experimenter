import sys
import unittest

from d3m.metadata.base import Context, ArgumentType
import d3m.utils as d3m_utils

from experimenter.pipeline_builder import EZPipeline, PipelineArchDesc


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
        self.assertEqual(pipeline.step_i_of('attrs'), 2)

        # setting a different ref should not affect an already set ref
        self.assertEqual(pipeline.data_ref_of('raw_df'), 'steps.0.produce')

        # Unset ref names should throw an error, rather than return a value.
        with self.assertRaises(Exception):
            pipeline.data_ref_of('Han Solo')
    
    def test_can_output_to_json(self) -> None:
        # Its important to ensure EZPipline can still
        # use the `d3m.metadata.pipeline.Pipeline.to_json_structure`
        # method.
        pipeline = self._make_no_steps_pipeline()

        self._add_dataset_to_df_step(pipeline)
        pipeline.set_step_i_of('raw_df')

        self._add_column_parser_step(pipeline)

        self._add_extract_attrs_step(pipeline)
        pipeline.set_step_i_of('attrs')

        json_rep = pipeline.to_json_structure()
        self.assertEqual(len(json_rep['steps']), 3)
    
    def test_arch_desc(self) -> None:
        architecture = PipelineArchDesc('test', { 'test_attr': None })
        pipeline = EZPipeline(arch_desc=architecture, context=Context.TESTING)
        pipeline.add_input(name='inputs')
        self._add_dataset_to_df_step(pipeline)
        
        # An architecture description should be able to be altered
        # once created
        pipeline.arch_desc.generation_parameters['other_test_attr'] = 'abc'

        # Pipeline should be valid in D3M's eyes, even with the custom
        # architecture description fields
        try:
            pipeline.check()
        except Exception as e:
            self.fail(f'pipeline is not a valid d3m pipeline: {repr(e)}')

        # The pipeline json should include the architecture description added above
        pipeline_json = pipeline.to_json_structure()
        self.assertIn('steps', pipeline_json)
        self.assertIn('pipeline_generation_description', pipeline_json)

        arch_desc_json = pipeline_json['pipeline_generation_description']
        self.assertIn('test_attr', arch_desc_json['generation_parameters'])
        self.assertIsNone(arch_desc_json['generation_parameters']['test_attr'])
        self.assertEqual(arch_desc_json['generation_parameters']['other_test_attr'], 'abc')

        # The pipeline's digest should be correct
        self.assertEqual(pipeline_json['digest'], d3m_utils.compute_digest(pipeline_json))
        
    # Private methods

    def _make_no_steps_pipeline(self) -> EZPipeline:
        pipeline = EZPipeline(context=Context.TESTING)
        pipeline.add_input(name='inputs')
        return pipeline

    def _add_dataset_to_df_step(self, pipeline: EZPipeline) -> None:
        pipeline.add_primitive_step(
            'd3m.primitives.data_transformation.dataset_to_dataframe.Common',
            'inputs.0'
        )

    def _add_column_parser_step(self, pipeline: EZPipeline) -> None:
        pipeline.add_primitive_step(
            'd3m.primitives.data_transformation.column_parser.DataFrameCommon'
        )
    
    def _add_extract_attrs_step(self, pipeline: EZPipeline) -> None:
        pipeline.add_primitive_step(
            'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon'
        )
        pipeline.current_step.add_hyperparameter(
            name='semantic_types',
            argument_type=ArgumentType.VALUE,
            data=['https://metadata.datadrivendiscovery.org/types/Attribute']
        )
