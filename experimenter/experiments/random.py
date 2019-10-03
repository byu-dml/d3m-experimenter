from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
from copy import copy
import random
import itertools

from d3m.metadata.pipeline import Pipeline, PrimitiveStep
from d3m.metadata.base import Context, ArgumentType
from d3m import index as d3m_index

from experimenter.experiments.experiment import Experiment
from experimenter.pipeline_builder import (
    EZPipeline, PipelineArchDesc, add_initial_steps, get_required_args, add_pipeline_step, add_predictions_constructor, map_pipeline_step_arguments
)
from experimenter.utils import multiply
from experimenter.constants import primitives_needing_gt_one_column

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
        # A mapping of data reference pairs to the data reference of their
        # concatenation.
        concat_cache: Dict[frozenset, str] = {}

        architecture = PipelineArchDesc(
            "random",
            { "depth": depth, "max_width": max_width, "max_num_inputs": max_num_inputs }
        )
        structure = EZPipeline(arch_desc=architecture, context=Context.TESTING)
        add_initial_steps(structure)
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

                concat_result_ref = self._concatenate_inputs(structure, input_refs, concat_cache)
                # Add the do nothing primitive as a placeholder. `self._sample_pipeline` will fill
                # in the primitives later.
                add_pipeline_step(
                    structure,
                    'd3m.primitives.data_preprocessing.do_nothing.DSBOX',
                    concat_result_ref
                )
                num_inputs_by_step[structure.curr_step_i] = num_inputs

                terminal_node_data_refs.add(structure.curr_step_data_ref)
                layer_outputs.add(structure.curr_step_data_ref)

            output_collection.update(layer_outputs)
        
        # Cleanup Phase

        # Route the output of all terminal nodes to a final primitive
        final_concat_ref = self._concatenate_inputs(structure, terminal_node_data_refs, concat_cache)
        add_pipeline_step(
            structure,
            'd3m.primitives.data_preprocessing.do_nothing.DSBOX',
            final_concat_ref
        )
        structure.set_step_i_of('final_model')

        add_predictions_constructor(structure)
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

                self._replace_step_at_i(structure, step_i, new_primitive_python_path)
        
        # Finally, make sure the last primitive before the construct predictions step
        # is a model.
        final_placeholder_step_i = structure.step_i_of('final_model')
        new_model_python_path, = random.sample(model_list, 1)
        self._replace_step_at_i(structure, final_placeholder_step_i, new_model_python_path)
        structure.steps[final_placeholder_step_i].hyperparams['return_result'] = {
            'type': ArgumentType.VALUE,
            'data': 'new',
        }

        return structure
    
    def _replace_step_at_i(
        self,
        pipeline: EZPipeline,
        step_i: int,
        new_step_python_path: str
    ) -> None:
        new_primitive = d3m_index.get_primitive(new_step_python_path)
        new_step = PrimitiveStep(primitive=new_primitive)
        old_step_inputs_data_ref = pipeline.steps[step_i].arguments['inputs']['data']
        # Fill in the new step's arguments
        map_pipeline_step_arguments(
            pipeline,
            new_step,
            get_required_args(new_primitive),
            # Preserve the inputs the old step was using.
            custom_data_ref=old_step_inputs_data_ref
        )
        pipeline.replace_step(step_i, new_step)

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
    
    def _find_match_in_cache(
        self, data_refs: Set[str],
        concat_cache: Dict[frozenset, str]
    ) -> Optional[frozenset]:
        """
        Uses all unordered combinations from `data_refs` (n choose k where k goes
        from n to 2) to find a match in `cache`, that is to say, a set of data refs in
        `data_refs` who have already been concatenated.

        :param data_refs: The set of data_refs to search in the cache for.
        :param concat_cache: The cache that maps data ref pairs to the data ref of
            their concatenated output.
        :return: If a match is found, the matching data ref pair is returned, else
            None is returned. 
        """
        for k in range(len(concat_cache), 1, -1):
            # Use all unordered combinations from `data_refs`
            # (n choose k where k goes from n to 2)
            for subset in itertools.combinations(data_refs, k):
                subset = frozenset(subset)
                if subset in concat_cache:
                    return subset
        return None
    
    def _concatenate_inputs(
        self,
        pipeline: EZPipeline,
        data_refs_to_concat: Set[str],
        concat_cache: Dict[frozenset, str]
    ) -> str:
        """
        Adds concatenation steps to `pipeline` that join the outputs of every data
        reference found in `data_refs_to_concat` until they are all a single data frame.

        :param pipeline: The pipeline the concatenation steps will be added to.
        :param data_refs_to_concat: The data references to the steps whose outputs are to be
            concatentated together.
        :param concat_cache: A cache holding data about previously concatenated outputs.
            If two steps in `data_refs_to_concat` have already been concatenated in another step on
            `pipeline`, then that concatenation step will be referenced during this
            concatenation, instead of creating a new duplicate concatenation step. Reduces
            the runtime and memory footprint of the pipeline.
        """
        if len(data_refs_to_concat) == 1:
            # No concatenation necessary
            output_data_ref, = data_refs_to_concat
            return output_data_ref
        
        data_refs = copy(data_refs_to_concat)

        while len(data_refs) > 1:
            # first look in `concat_cache` for an already existing
            # concatenation we can use.
            cache_match = self._find_match_in_cache(data_refs, concat_cache)
            
            if cache_match is None:
                # Manually concatenate a pair of data refs, then add them to the cache.
                data_ref_pair = sorted(data_refs)[:2]
                concat_step = self._build_concatenate_step(*data_ref_pair)
                pipeline.add_step(concat_step)
                concat_data_ref = pipeline.curr_step_data_ref

                # Save the link between the data ref pair and their concatenation's
                # output to the `concat_cache`.
                data_ref_pair = frozenset(data_ref_pair)
                concat_cache[data_ref_pair] = concat_data_ref
                # Now we have a match in the cache.
                cache_match = data_ref_pair

            # Now that we've concatenated `data_ref_pair`, we don't
            # need it in `data_refs` anymore.
            data_refs -= cache_match
            data_refs.add(concat_cache[cache_match])
        
        output_data_ref, = data_refs
        return output_data_ref
    
    def _build_concatenate_step(self, left_data_ref: str, right_data_ref: str) -> PrimitiveStep:
        concat_step = PrimitiveStep(
            primitive=d3m_index.get_primitive('d3m.primitives.data_transformation.horizontal_concat.DataFrameConcat')
        )
        concat_step.add_argument(name='left', argument_type=ArgumentType.CONTAINER, data_reference=left_data_ref)
        concat_step.add_argument(name='right', argument_type=ArgumentType.CONTAINER, data_reference=right_data_ref)
        concat_step.add_output('produce')
        return concat_step
