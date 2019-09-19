from typing import Tuple, List

from d3m import index as d3m_index
from d3m.metadata.pipeline import Pipeline
from d3m.metadata.pipeline import PrimitiveStep
from d3m.metadata.base import ArgumentType

class EZPipeline(Pipeline):
    """
    A subclass of `d3m.metadata.pipeline.Pipeline` that is easier to work
    with when building a pipeline, since it allows for certain steps to be
    tagged with a 'ref', (a.k.a. reference) so they can be easily referenced
    later on in the building of the pipeline. For example an `EZPipeline`
    can be used to track which step contains the pipeline's raw dataframe,
    prepared attributes, prepared targets, etc., and to easily get access to
    those steps and their output when future steps need to use the output of
    those steps as input.
    """

    # Constructor

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The indices of the steps that each ref is associated with.
        # All begin with `None`, just like the value of `self.curr_step_i`.
        self._step_i_of_refs = { name: None for name in self.valid_ref_names }
    
    # Public properties

    @property
    def valid_ref_names(self) -> Tuple[str]:
        return ('raw_target', 'target', 'raw_df', 'raw_attrs', 'attrs')

    @property
    def curr_step_i(self) -> None:
        """
        Returns the current step index i.e. the index of the step
        most recently added to the pipeline.
        """
        num_steps = len(self.steps)
        return None if num_steps == 0 else num_steps - 1
    
    @property
    def curr_step_data_ref(self) -> str:
        return self._data_ref_by_step_i(self.curr_step_i)
    
    # Public methods

    def set_step_i_of(self, ref_name: str, step_i: int = None) -> None:
        """
        Sets the step index of the ref identified by `ref_name`.
        If `step_i` is `None`, the ref's step index will be set to the
        index of the current step.
        """
        self._validate_ref_name(ref_name)
        if step_i is None:
            self._step_i_of_refs[ref_name] = self.curr_step_i
        else:
            self._step_i_of_refs[ref_name] = step_i
            
    
    def data_ref_of(self, ref_name: str) -> str:
        """
        Returns a data reference to the output of the step associated
        with `ref_name`. For example if the step index of the `raw_attrs`
        ref is 2, and the output method name of step 2 is 'produce',
        then `data_ref_of('raw_attrs')` == 'step.2.produce'`.
        """
        self._validate_ref_name(ref_name)
        ref_step_i = self._step_i_of_refs[ref_name]
        if ref_step_i is None:
            raise ValueError(f'{ref_name} has not been set yet')
        return self._data_ref_by_step_i(ref_step_i)
    
    # Private methods
    
    def _validate_ref_name(self, ref_name: str) -> None:
        if ref_name not in self.valid_ref_names:
            raise ValueError(f'{ref_name} is not a valid ref name')
    
    def _data_ref_by_step_i(self, step_i: int) -> str:
        step_output_names: List[str] = self.steps[step_i].outputs
        if len(step_output_names) != 1:
            raise AttributeError(
                f'step {step_i} has more than one output; which output to use is ambiguous'
            )
        return f'steps.{step_i}.{step_output_names[0]}'


def create_pipeline_step(
    python_path: str,
    input_data_reference: str,
    *,
    input_argument_type: ArgumentType = ArgumentType.CONTAINER,
    output_name: str = 'produce'
) -> PrimitiveStep:
    """
    Helper for creating a d3m.metadata.pipeline.PrimitiveStep in a less verbose manner.

    :param python_path: the python path of the primitive to be added.
    :param input_data_reference: a data reference string to use for the primitive's inputs.
    :param input_argument_type: an optional input argument type to use for the primitive.
    :param output_name: an optional method output name to use for the primitive.
    
    :return step: the constructed primitive step.
    """
    
    step = PrimitiveStep(
        primitive=d3m_index.get_primitive(python_path))
    step.add_argument(
        name='inputs',
        argument_type=input_argument_type,
        data_reference=input_data_reference
    )
    step.add_output(output_name)

    return step

def add_pipeline_step(
    pipeline_description: EZPipeline,
    python_path: str,
    input_data_reference: str = None,
    **kwargs
) -> int:
    """
    A helper method. Adds the results of `create_pipeline_step` to `pipeline_description`,
    returning the updated step counter.

    :param pipeline_description: The pipeline to add a step to.
    :param python_path: the python path of the primitive to be added.
    :param input_data_reference: an optional data reference string to use for the primitive's inputs.
        If `None`, the output data reference to the pipeline's most recently added step will be used. 
    :param **kwargs: any other keyword arguments to pass to `create_pipeline_step`

    :return: The updated step counter
    """
    if input_data_reference is None:
        input_data_reference = pipeline_description.curr_step_data_ref
    step = create_pipeline_step(python_path, input_data_reference, **kwargs)
    pipeline_description.add_step(step)
