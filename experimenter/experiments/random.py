from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
from copy import copy
import random
import itertools

from d3m.metadata.pipeline import Pipeline, PrimitiveStep
from d3m.metadata.base import Context, ArgumentType

from experimenter.experiments.experiment import Experiment
from experimenter.pipeline_builder import EZPipeline, PipelineArchDesc
from experimenter.utils import multiply
from experimenter.constants import primitives_needing_gt_one_column, d3m_index

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
        n_structures: int,
        n_pipelines_per_structure: int,
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
        :param n_structures: The number of pipeline structures to sample from the
            random architecture space.
        :param n_pipelines_per_structure: The number of pipelines to make for each
            structure. Each pipeline's primitives will be sampled from
            `preprocessors` and `models`, so the probability of pipelines using the
            same sequence of primitives is low.
        :param depth_sample_range: An integer range to sample from to determine the
            depth of each pipeline structure.
        :param max_width_sample_range: An integer range to sample from to determine
            a 'layer width' sample range for each pipeline structure.
        :param max_inputs_sample_range: An integer range to sample from to determine
            a 'number of inputs' sample range for each pipeline structure.
        :param max_complexity_factor: For each structure sampled, the structure's
            `depth * max_width * max_num_inputs` will not exceed this value.
        :return: A dict containing two keys of `classification` and `regression` each a
            list of pipeline objects. Each list will have `n_structures *
            n_pipelines_per_structure` total pipelines.
        """
        generated_pipelines: Dict[str, List[Pipeline]] = defaultdict(list)
        for type_name, model_list in models.items():

            # Sample the structures
            structures = []
            for _ in range(n_structures):
                depth, max_width, max_num_inputs = self._sample_parameters(
                    [depth_sample_range, max_width_sample_range, max_inputs_sample_range],
                    max_complexity_factor
                )
                structures.append(self._sample_structure(depth, max_width, max_num_inputs))

            # Sample pipelines from each structure
            for structure, num_inputs_by_step in structures:
                for _ in range(n_pipelines_per_structure):
                    generated_pipelines[type_name].append(
                        self._sample_pipeline(structure, preprocessors, model_list, num_inputs_by_step)
                    )
        
        return generated_pipelines
    
    def generate_pipeline(
        self,
        preprocessors: List[str],
        model_list: List[str],
        depth: int,
        max_width: int,
        max_num_inputs: int
    ) -> EZPipeline:
        """
        Similar to `self.generate_pipelines`, but generates a single pipeline from
        a single random structure.Also, doesn't take sample ranges, but a `depth`,
        `max_width`, and `max_num_inputs` directly.

        :param preprocessors: A list of preprocessor primitive python paths.
        :param model_list: A list of ML model (e.g. random forest, knn, etc.)
            primitive python paths.
        :param depth: The depth the pipeline structure will have i.e. the number
            of layers.
        :param max_width: The maximum width for each layer in the structure.
        :param max_num_inputs: The maximum number of inputs each primitive in the
            structure will have.
        """
        structure, num_inputs_by_step = self._sample_structure(depth, max_width, max_num_inputs)
        pipeline = self._sample_pipeline(structure, preprocessors, model_list, num_inputs_by_step)
        return pipeline

    
    # Private methods

    def _sample_structure(self, depth: int, max_width: int, max_num_inputs: int) -> Tuple[EZPipeline, Dict[int, int]]:
        """
        :param depth: The depth the pipeline structure will have i.e. the number
            of layers.
        :param max_width: The maximum width for each layer in the structure.
        :param max_num_inputs: The maximum number of inputs each primitive in the
            structure will have.
        """

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
        # Keeps track of the number of inputs each step is using
        num_inputs_by_step: Dict[int, int] = defaultdict(int)

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
                # Add the do nothing primitive as a placeholder. `self._sample_pipeline` will fill
                # in the primitives later.
                structure.add_primitive_step(
                    'd3m.primitives.data_preprocessing.do_nothing.DSBOX',
                    concat_result_ref
                )
                num_inputs_by_step[structure.curr_step_i] = num_inputs

                terminal_node_data_refs.add(structure.curr_step_data_ref)
                layer_outputs.add(structure.curr_step_data_ref)

            output_collection.update(layer_outputs)
        
        # Cleanup Phase

        # Route the output of all terminal nodes to a final primitive
        final_concat_ref = structure.concatenate_inputs(*terminal_node_data_refs)
        structure.add_primitive_step(
            'd3m.primitives.data_preprocessing.do_nothing.DSBOX',
            final_concat_ref
        )
        structure.set_step_i_of('final_model')

        structure.add_predictions_constructor()
        # Adding output step to the pipeline
        structure.add_output(name='Output', data_reference=structure.curr_step_data_ref)
        return structure, num_inputs_by_step
    
    def _sample_pipeline(
        self,
        structure: EZPipeline,
        preprocessors: List[str],
        model_list: List[str],
        num_inputs_by_step: Dict[int, int]
    ) -> EZPipeline:
        """
        :param structure: An `EZPipeline`. Every step in `structure` that uses
            a do nothing primitive will be replaced with a primitive sampled from
            `preprocessors` and `model_list`.
        :param preprocessors: A list of preprocessor primitive python paths.
        :param model_list: A list of ML model (e.g. random forest, knn, etc.)
            primitive python paths.
        :param num_inputs_by_step: A map of `structure`'s step indices to the
            number of inputs each of those steps have.
        """
        all_primitives = set(preprocessors + model_list)
        primitives_that_can_handle_one_input_column = all_primitives - primitives_needing_gt_one_column

        # Replace all placeholder primitives with randomly sampled preprocessors
        # and models
        for step_i, old_step in enumerate(structure.steps):
            if old_step.primitive.metadata.query()["python_path"] == 'd3m.primitives.data_preprocessing.do_nothing.DSBOX':

                # This is a placeholder primitive that's to be filled in by a new step.
                if num_inputs_by_step[step_i] == 1:
                    # There's a chance this primitive will only be taking one input column
                    new_primitive_python_path, = random.sample(primitives_that_can_handle_one_input_column, 1)
                else:
                    new_primitive_python_path, = random.sample(all_primitives, 1)

                structure.replace_step_at_i(step_i, new_primitive_python_path)
        
        # Finally, make sure the last primitive before the construct predictions step
        # is a model.
        final_placeholder_step_i = structure.step_i_of('final_model')
        new_model_python_path, = random.sample(model_list, 1)
        structure.replace_step_at_i(final_placeholder_step_i, new_model_python_path)

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
