from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
from copy import copy
import itertools

from d3m.metadata.pipeline import Pipeline, PrimitiveStep
from d3m.metadata.base import Context, ArgumentType

from experimenter.experiments.experiment import Experiment
from experimenter.pipeline_builder import EZPipeline, PipelineArchDesc
from experimenter.utils import multiply
from experimenter.constants import primitives_needing_gt_one_column
from experimenter.config import d3m_index, random

class RandomArchitectureExperimenter(Experiment):
    """
    Generates diverse pipelines of random architectures.
    """

    # Public methods

    def generate_pipelines(
        self,
        *,
        preprocessors: List[str],
        models: Dict[str,str],
        n_pipelines: int,
        depth_sample_range: Tuple[int, int],
        max_width_sample_range: Tuple[int, int],
        max_inputs_sample_range: Tuple[int, int],
        max_complexity_factor: int,
        **unused_args

    ) -> Dict[str, List[Pipeline]]:
        """
        :param preprocessors: A list of preprocessor primitive python paths to
            use to generate pipelines with.
        :param models: A dict containing two keys of `classification` and `regression`
            each with a list of model primitive python paths.
        :param n_pipelines: The number of pipelines to sample from the random
            architecture space.
        :param depth_sample_range: An integer range to sample from to determine the
            depth of each pipeline structure.
        :param max_width_sample_range: An integer range to sample from to determine
            a 'layer width' sample range for each pipeline structure.
        :param max_inputs_sample_range: An integer range to sample from to determine
            a 'number of inputs' sample range for each pipeline structure.
        :param max_complexity_factor: For each structure sampled, the structure's
            `depth * max_width * max_num_inputs` will not exceed this value.
        :return: A dict containing two keys of `classification` and `regression` each a
            list of pipeline objects. Each list will have `n_pipelines` total pipelines.
        """
        generated_pipelines: Dict[str, List[Pipeline]] = defaultdict(list)
        for type_name, model_list in models.items():

            # Sample the pipelines
            for _ in range(n_pipelines):
                depth, max_width, max_num_inputs = self._sample_parameters(
                    [depth_sample_range, max_width_sample_range, max_inputs_sample_range],
                    max_complexity_factor
                )
                generated_pipelines[type_name].append(
                    self.generate_pipeline(preprocessors, model_list, depth, max_width, max_num_inputs)
                )
        
        return generated_pipelines
    
    # Private methods

    def generate_pipeline(
        self,
        preprocessors: List[str],
        model_list: List[str],
        depth: int,
        max_width: int,
        max_num_inputs: int
    ) -> Tuple[EZPipeline, Dict[int, int]]:
        """
        :param depth: The depth the pipeline structure will have i.e. the number
            of layers.
        :param max_width: The maximum width for each layer in the structure.
        :param max_num_inputs: The maximum number of inputs each primitive in the
            structure will have.
        """
        all_primitives = set(preprocessors + model_list)
        primitives_that_can_handle_one_input_column = all_primitives - primitives_needing_gt_one_column

        architecture = PipelineArchDesc(
            "random",
            { "depth": depth, "max_width": max_width, "max_num_inputs": max_num_inputs }
        )
        structure = EZPipeline(
            arch_desc=architecture,
            add_preparation_steps=True,
            context=Context.TESTING
        )
        # The running collection of all step data references that can
        # be used as inputs for subsequent primitives in the pipeline. 
        output_collection: Set[str] = { structure.data_ref_of('attrs') }
        terminal_node_data_refs: Set[str] = set()

        # Pipeline Build Phase

        for _ in range(depth):
            layer_width = random.randint(1, max_width)
            layer_outputs: Set[str] = set()
            for _ in range(layer_width):
                
                num_inputs = random.randint(1, max_num_inputs)
                # There are only `len(output_collection)` possible inputs available.
                num_inputs = min(len(output_collection), num_inputs)
                input_refs: Set[str] = set(random.sample(output_collection, num_inputs))

                # Since the steps identified by `input_refs` are now being used
                # as inputs, we know they're not terminal nodes anymore.
                terminal_node_data_refs -= input_refs

                concat_result_ref = structure.concatenate_inputs(*input_refs)

                # Randomly sample a preprocessor or model to use for this node.
                if num_inputs == 1:
                    # There's a chance this primitive will only be taking one input column
                    primitive_python_path, = random.sample(primitives_that_can_handle_one_input_column, 1)
                else:
                    primitive_python_path, = random.sample(all_primitives, 1)
                
                structure.add_primitive_step(
                    primitive_python_path,
                    concat_result_ref,
                    is_final_model=False
                )

                terminal_node_data_refs.add(structure.curr_step_data_ref)
                layer_outputs.add(structure.curr_step_data_ref)

            # Make this layer's outputs available to the next layer
            # as inputs.
            output_collection.update(layer_outputs)
        
        # Cleanup Phase

        # Route the output of all terminal nodes to a final primitive
        final_concat_ref = structure.concatenate_inputs(*terminal_node_data_refs)
        model_python_path, = random.sample(model_list, 1)
        structure.add_primitive_step(model_python_path, final_concat_ref)
        structure.set_step_i_of('final_model')

        structure.add_predictions_constructor()
        # Adding output step to the pipeline
        structure.add_output(name='Output', data_reference=structure.curr_step_data_ref)
        return structure

    def _sample_parameters(self, ranges: List[Tuple[int, int]], max_sample_prod: int) -> Tuple[int, ...]:
        """
        :param ranges: A list of integer ranges. Each will be sampled from uniformly.
        :param max_sample_prod: A maximum threshold for the product of all
            sampled values. Sampling will keep occuring until samples falling within
            this threshold are produced.
        :return: A tuple contained a sample for each of the sample ranges in `ranges`.
        """
        samples = tuple(random.randint(*rng) for rng in ranges)
        while multiply(samples) > max_sample_prod:
            samples = tuple(random.randint(*rng) for rng in ranges)
        return samples
