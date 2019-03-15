from d3m import index as d3m_index
from d3m.metadata import base as metadata_base
from d3m.metadata.pipeline import Pipeline, PrimitiveStep

from .primitives import AutoSklearnClassifierPrimitive

def get_classification_pipeline(time_limit=20):
    pipeline_description = Pipeline(context=metadata_base.Context.TESTING)
    pipeline_description.add_input(name='inputs')

    # 0 Denormalize Dataset
    denormalize_primitive: PrimitiveBase = d3m_index.get_primitive(
        'd3m.primitives.data_transformation.denormalize.Common'
    )
    step_0 = PrimitiveStep(primitive=denormalize_primitive)
    step_0.add_argument(
        name='inputs', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='inputs.0'
    )
    step_0.add_output('produce')
    pipeline_description.add_step(step_0)

    # 1 Dataset to DataFrame
    dataset_to_dataframe_primitive = d3m_index.get_primitive(
        'd3m.primitives.data_transformation.dataset_to_dataframe.Common'
    )
    step_1 = PrimitiveStep(primitive=dataset_to_dataframe_primitive)
    step_1.add_argument(
        name='inputs', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='steps.0.produce'
    )
    step_1.add_output('produce')
    pipeline_description.add_step(step_1)

    # 2 Column Parser
    column_parser_primitive = d3m_index.get_primitive(
        'd3m.primitives.data_transformation.column_parser.DataFrameCommon'
    )
    step_2 = PrimitiveStep(primitive=column_parser_primitive)
    step_2.add_argument(
        name='inputs', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='steps.1.produce'
    )
    step_2.add_output('produce')
    pipeline_description.add_step(step_2)

    # 3 Label Encoder
    label_encoder_primitive = d3m_index.get_primitive(
        'd3m.primitives.data_preprocessing.label_encoder.DataFrameCommon'
    )
    step_3 = PrimitiveStep(primitive=label_encoder_primitive)
    step_3.add_argument(
        name='inputs', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='steps.2.produce'
    )
    step_3.add_output('produce')
    pipeline_description.add_step(step_3)

    # Step 4: extract_columns_by_semantic_types(attributes)
    extract_columns_primitive = d3m_index.get_primitive(
        'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon'
    )
    step_4 = PrimitiveStep(primitive=extract_columns_primitive)
    step_4.add_argument(
        name='inputs', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='steps.3.produce'
    )
    step_4.add_output('produce')
    step_4.add_hyperparameter(
        name='semantic_types', argument_type=metadata_base.ArgumentType.VALUE,
        data=['https://metadata.datadrivendiscovery.org/types/Attribute']
    )
    pipeline_description.add_step(step_4)

    # Step 5: extract_columns_by_semantic_types(targets)
    step_5 = PrimitiveStep(primitive=extract_columns_primitive)
    step_5.add_argument(
        name='inputs', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='steps.3.produce'
    )
    step_5.add_output('produce')
    step_5.add_hyperparameter(
        name='semantic_types', argument_type=metadata_base.ArgumentType.VALUE,
        data=['https://metadata.datadrivendiscovery.org/types/TrueTarget']
    )
    pipeline_description.add_step(step_5)

    # 6 AutoSKLearn Classifier
    autosklearn_classifier_primitive = d3m_index.get_primitive(
        'd3m.primitives.classification.search.AutoSKLearn'
    )
    step_6 = PrimitiveStep(primitive=autosklearn_classifier_primitive)
    step_6.add_argument(
        name='inputs', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='steps.4.produce'
    )
    step_6.add_argument(
        name='outputs', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='steps.5.produce'
    )
    step_6.add_hyperparameter(
        name='time_left_for_this_task', argument_type=metadata_base.ArgumentType.VALUE,
        data=time_limit
    )
    step_6.add_output('produce')
    pipeline_description.add_step(step_6)

    # 7 construct predictions
    predictions_constructor: PrimitiveBase = d3m_index.get_primitive(
        'd3m.primitives.data_transformation.construct_predictions.DataFrameCommon'
    )
    step_7 = PrimitiveStep(primitive=predictions_constructor)
    step_7.add_argument(
        name='inputs', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='steps.6.produce'
    )
    step_7.add_argument(
        name='reference', argument_type=metadata_base.ArgumentType.CONTAINER,
        data_reference='steps.2.produce'
    )
    step_7.add_output('produce')
    pipeline_description.add_step(step_7)

    # pipeline outputs
    pipeline_description.add_output(
        name='output', data_reference='steps.7.produce'
    )

    return pipeline_description
