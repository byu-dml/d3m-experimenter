from d3m import index as d3m_index
from d3m.metadata.pipeline import Pipeline
from d3m.metadata.pipeline import PrimitiveStep
from d3m.metadata.base import ArgumentType

def create_pipeline_step(
    step_counter: int,
    python_path: str,
    *,
    input_data_reference: str = None,
    input_argument_type: ArgumentType = ArgumentType.CONTAINER,
    output_name: str = 'produce'
) -> PrimitiveStep:
    """
    Helper for creating a d3m.metadata.pipeline.PrimitiveStep in a less verbose manner.

    :param step_counter: an integer representing the step number this call will create.
    :param python_path: the python path of the primitive to be added.
    :param input_data_reference: an optional custom data reference string for the primitive's inputs.
        If not provided, the default will be `'steps.{step_counter - 1}.produce'`, i.e. the output
        of the previous step.
    :param input_argument_type: an optional input argument type to use for the primitive.
    :param output_name: an optional method output name to use for the primitive.
    
    :return step: the constructed primitive step.
    """
    if input_data_reference is None:
        input_data_reference = f'steps.{step_counter - 1}.produce'
    
    step = PrimitiveStep(
        primitive=d3m_index.get_primitive(python_path))
    step.add_argument(
        name='inputs',
        argument_type=input_argument_type,
        data_reference=input_data_reference
        )
    step.add_output(output_name)

    return step

def add_pipeline_step(pipeline_description: Pipeline, step_counter: int, *args, **kwargs) -> int:
    """
    A helper method. Adds the results of `create_pipeline_step` to `pipeline_description`,
    returning the updated step counter.

    :param pipeline_description: The pipeline to add a step to.
    :param step_counter: an integer representing the step number this call will create.
    :param *args: The rest of the positional args to forward to `create_pipeline_step`.
    :param **kwargs: The rest of the keyword args to forward to `create_pipeline_step`.

    :return: The updated step counter
    """
    step = create_pipeline_step(step_counter, *args, **kwargs)
    pipeline_description.add_step(step)
    return step_counter + 1
