from typing import Tuple, List, Any, Dict

from d3m import utils as d3m_utils, index as d3m_index
from d3m.metadata.pipeline import Pipeline
from d3m.metadata.pipeline import PrimitiveStep
from d3m.metadata.base import ArgumentType
from d3m.primitive_interfaces.base import PrimitiveBase

from experimenter.constants import EXTRA_HYPEREPARAMETERS


class PipelineArchDesc:
    """
    Holds data that describes a pipeline's architecture. e.g.
    `PipelineArchDesc(generation_method="ensemble", generation_parameters={"k": 3}) could
    describe an ensemble pipeline that ensembles three classifiers.
    """

    def __init__(self, generation_method: str, generation_parameters: Dict[str, Any] = None):
        """
        :param generation_method: The pipeline's high level structural type e.g.
            "ensemble", "straight", "random", etc.
        :param generation_parameters: An optional dictionary holding data describing
            attributes of the pipeline's architecture e.g.
            { "depth": 4, "max_width": 3 }, etc. Fields in the dictionary
            will likely vary depending on the pipeline's type.
        """
        self.generation_method = generation_method
        self.generation_parameters = dict() if generation_parameters is None else generation_parameters
    
    def to_json_structure(self):
        return {
            "generation_method": self.generation_method,
            "generation_parameters": self.generation_parameters
        }


class EZPipeline(Pipeline):
    """
    A subclass of `d3m.metadata.pipeline.Pipeline` that is easier to work
    with when building a pipeline, since it allows for certain steps to be
    tagged with a 'ref', (a.k.a. reference) so they can be easily referenced
    later on in the building of the pipeline. For example it can be used to
    track which steps contain the pipeline's raw dataframe, prepared
    attributes, prepared targets, etc., and to easily get access to those
    steps and their output when future steps need to use the output of those
    steps as input.
    """

    # Constructor

    def __init__(self, *args, arch_desc: PipelineArchDesc = None, **kwargs):
        """
        :param *args: All positional args are forwarded to the superclass
            constructor.
        :param arch_desc: an optional description of the pipeline's
        architecture.
        :param **kwargs: All other keyword args are forwarded to the
        superclass constructor.
        """
        super().__init__(*args, **kwargs)
        # The indices of the steps that each ref is associated with.
        # All begin with `None`, just like the value of `self.curr_step_i`.
        self._step_i_of_refs: Dict[str, int] = {}
        self.arch_desc = arch_desc
    
    # Public properties

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
        if step_i is None:
            self._step_i_of_refs[ref_name] = self.curr_step_i
        else:
            self._step_i_of_refs[ref_name] = step_i
            
    def step_i_of(self, ref_name: str) -> int:
        """
        Returns the index of the step associated with `ref_name`.
        """
        self._check_ref_is_set(ref_name)
        return self._step_i_of_refs[ref_name]
    

    def data_ref_of(self, ref_name: str) -> str:
        """
        Returns a data reference to the output of the step associated
        with `ref_name`. For example if the step index of the `raw_attrs`
        ref is 2, and the output method name of step 2 is 'produce',
        then `data_ref_of('raw_attrs')` == 'step.2.produce'`.
        """
        return self._data_ref_by_step_i(self.step_i_of(ref_name))
    
    def to_json_structure(self, *args, **kwargs) -> Dict:
        """
        An overriden version of the parent class `Pipeline`'s method.
        Adds the pipeline architecture description to the json.
        """
        pipeline_json = super().to_json_structure(*args, **kwargs)
        if self.arch_desc is not None:
            pipeline_json['pipeline_generation_description'] = self.arch_desc.to_json_structure()
            # Update the digest since new information has been added to the description
            pipeline_json['digest'] = d3m_utils.compute_digest(pipeline_json)
        
        return pipeline_json

    
    # Private methods
    
    def _check_ref_is_set(self, ref_name: str) -> None:
        if ref_name not in self._step_i_of_refs:
            raise ValueError(f'{ref_name} has not been set yet')
    
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


def map_pipeline_step_arguments(
    pl: EZPipeline,
    step: PrimitiveStep,
    required_args: list,
    use_current_step_data_ref: bool = False,
    custom_data_ref: str = None
) -> None:
    """
    Helper used to add arguments to a PrimitiveStep.

    :param pl: The pipeline to which step belongs.
    :param step: The pipeline step to add arguments and hyperparameters to.
        Either a preprocessor or a classifier.
    :param required_args: The required arguments for step.
    :param use_current_step_data_ref: For arguments other than 'outputs', this
        boolean indicates whether to use the data reference of the current step
        rather than 'attrs'.
    :param custom_data_ref: If provided, this will be used as the data reference
        for all arguments other than 'outputs'.

    :rtype: None
    """
    for arg in required_args:
        if arg == "outputs":
            data_ref = pl.data_ref_of('target')
        else:
            if custom_data_ref:
                data_ref = custom_data_ref
            elif use_current_step_data_ref:
                data_ref = pl.curr_step_data_ref
            else:
                data_ref = pl.data_ref_of('attrs')

        step.add_argument(name=arg, argument_type=ArgumentType.CONTAINER,
                            data_reference=data_ref)
    step.add_hyperparameter(name='return_result', argument_type=ArgumentType.VALUE, data="new")

    # handle any extra hyperparams needed
    step_python_path = step.primitive.metadata.query()["python_path"]
    if step_python_path in EXTRA_HYPEREPARAMETERS:
        params = EXTRA_HYPEREPARAMETERS[step_python_path]
        for param in params:
            step.add_hyperparameter(name=param["name"], argument_type=param["type"], data=param["data"])
    step.add_output('produce')


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
    

def add_initial_steps(pipeline_description: EZPipeline) -> None:
    """
    :param pipeline_description: an empty pipeline object that we can add
        the initial data preparation steps to.
    """
    # Creating pipeline
    pipeline_description.add_input(name='inputs')

    # dataset_to_dataframe step
    add_pipeline_step(
        pipeline_description,
        'd3m.primitives.data_transformation.dataset_to_dataframe.Common',
        'inputs.0'
    )
    pipeline_description.set_step_i_of('raw_df')

    # column_parser step
    add_pipeline_step(
        pipeline_description,
        'd3m.primitives.data_transformation.column_parser.DataFrameCommon'
    )

    # imputer step
    add_pipeline_step(
        pipeline_description,
        'd3m.primitives.data_preprocessing.random_sampling_imputer.BYU'
    )

    # extract_columns_by_semantic_types(attributes) step
    extract_attributes_step = create_pipeline_step(
        'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon',
        pipeline_description.curr_step_data_ref
    )
    extract_attributes_step.add_hyperparameter(name='semantic_types', argument_type=ArgumentType.VALUE,
                                data=['https://metadata.datadrivendiscovery.org/types/Attribute'])
    pipeline_description.add_step(extract_attributes_step)
    pipeline_description.set_step_i_of('attrs')

    # extract_columns_by_semantic_types(targets) step
    extract_targets_step = create_pipeline_step(
        'd3m.primitives.data_transformation.extract_columns_by_semantic_types.DataFrameCommon',
        pipeline_description.data_ref_of('raw_df')
    )
    extract_targets_step.add_hyperparameter(name='semantic_types', argument_type=ArgumentType.VALUE,
                                data=['https://metadata.datadrivendiscovery.org/types/TrueTarget'])
    pipeline_description.add_step(extract_targets_step)
    pipeline_description.set_step_i_of('target')


def add_predictions_constructor(pipeline_description: EZPipeline, input_data_ref: str = None) -> None:
    """
    Adds the predictions constructor to a pipeline description
    :param pipeline_description: the pipeline-to-be
    :param input_data_ref: the data reference to be used as the input to the predictions primitive.
        If `None`, the output data reference to the pipeline's most recently added step will be used. 
    """
    if input_data_ref is None:
        input_data_ref = pipeline_description.curr_step_data_ref
    # PredictionsConstructor step
    step = create_pipeline_step(
        "d3m.primitives.data_transformation.construct_predictions.DataFrameCommon",
        input_data_ref
    )
    step.add_argument(
        name='reference',
        argument_type=ArgumentType.CONTAINER,
        data_reference=pipeline_description.data_ref_of('raw_df')
    )
    pipeline_description.add_step(step)


def get_required_args(p: PrimitiveBase) -> list:
    """
    Gets the required arguments for a primitive
    :param p: the primitive to get arguments for
    :return a list of the required args
    """
    required_args = []
    metadata_args = p.metadata.to_json_structure()['primitive_code']['arguments']
    for arg, arg_info in metadata_args.items():
        if 'default' not in arg_info and arg_info['kind'] == 'PIPELINE':  # If yes, it is a required argument
            required_args.append(arg)
    return required_args
