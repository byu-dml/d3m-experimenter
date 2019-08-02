import json
import typing

from d3m import exceptions, container
from d3m.metadata import (base as metadata_base, problem as base_problem, pipeline as pipeline_module,
                          pipeline_run as pipeline_run_module)
from d3m.metadata.pipeline_run import RuntimeEnvironment
from d3m.container.dataset import ComputeDigest
from d3m.runtime import fit, get_dataset, Runtime



class RunFitPipeline:
    """
    In this function we define all the parameters needed to actually execute the pipeline.

    :param datasets_dir: a string denoting the base directory containing all the datasets. For example `/datasets`
    :param volumes_dir: a string denoting the volumes directory, used by the runtime.
    :param pipeline_path: a string containing the full path to the pipeline file to be used (JSON or YML file)
    :param problem_path: a string containing the path to the given problem
    :param output_path: an optional parameter specifying the location to place the finished pipeline_run file.  If it
        is empty no output path is used.
    """

    def __init__(self, datasets_dir: str, volumes_dir: str, problem_path: str, output_path: str = None):
        self.datasets_dir = datasets_dir
        self.volumes_dir = volumes_dir
        self.data_pipeline_path = './experimenter/pipelines/fixed-split-tabular-split.yml'
        self.scoring_pipeline_path = './experimenter/pipelines/scoring.yml'
        self.output_path = output_path
        self.problem_path = problem_path
        self.problem_name = self.problem_path.split("/")[-1]

        # Note that most of these are not needed but included in case it is useful someday
        self.run_args = {"scoring_pipeline": self.scoring_pipeline_path,
                         'data_pipeline': self.data_pipeline_path,
                         'data_split_file': '{}/{}_problem/dataSplits.csv'.
                             format(self.problem_path, self.problem_name),
                         'problem': '{}/{}_problem/problemDoc.json'.
                             format(self.problem_path, self.problem_name),
                         'inputs': ['{}/{}_dataset/datasetDoc.json'.
                                        format(self.problem_path, self.problem_name)],
                         "context": metadata_base.Context.PRODUCTION
                         }


    def run(self, pipeline: pipeline_module.Pipeline, random_seed: int = 0) -> list:
         """
        This function is what actually executes the pipeline, splits it, and returns the final predictions and scores. 
        Note that this function is EXTREMELY simimlar to that of `_evaluate` in the Runtime code. The aforementioned
        function does not allow for returning the data, so it did not fit in the workflow.

        :param pipeline: the pipeline object to be run OR the path to the pipeline file to be used
        :param random_seed: the random seed that the runtime will use to evalutate the pipeline
        :returns results_list: a list containing, in order, scores from the pipeline predictions, the fit pipeline_run 
            and the produce pipeline_run.
        """
        arguments = self.run_args

        runtime_environment = RuntimeEnvironment()

        dataset_resolver = get_dataset

        context = metadata_base.Context[arguments["context"]]

        problem_description = base_problem.parse_problem_description(arguments["problem"])

        inputs = [
            dataset_resolver(
                input_uri,
                compute_digest=ComputeDigest[ComputeDigest.ONLY_IF_MISSING.name],
                strict_digest=False,
            )
            for input_uri in arguments['inputs']
        ]

        print(inputs)

        try:
            runtime, outputs, results_list = self.our_fit(
                pipeline, problem_description, inputs,
                context=context, random_seed=random_seed,
                volumes_dir=self.volumes_dir,
                runtime_environment=runtime_environment,
            )
        except exceptions.PipelineRunError as error:
            print("ERROR: {}".format(error.pipeline_runs))
            raise error

        return results_list


    def our_fit(self, pipeline: pipeline_module.Pipeline, problem_description: typing.Dict, inputs: typing.Sequence[container.Dataset], *,
    context: metadata_base.Context, hyperparams: typing.Sequence = None, random_seed: int = 0, volumes_dir: str = None,
    runtime_environment: pipeline_run_module.RuntimeEnvironment = None,
    ) -> typing.Tuple[Runtime, container.DataFrame, pipeline_run_module.PipelineRun]:
        """
        Our version of D3M's fit so that we can modify it. See the D3M module for documentation
        """
        for input in inputs:
            if not isinstance(input, container.Dataset):
                raise TypeError(
                    "A standard pipeline's input should be of a container Dataset type, not {input_type}.".format(
                        input_type=type(input),
                    ))

        if len(pipeline.outputs) != 1:
            raise ValueError("A standard pipeline should have exactly one output, not {outputs}.".format(
                outputs=len(pipeline.outputs),
            ))

        runtime = Runtime(
            pipeline, hyperparams,
            problem_description=problem_description, context=context,
            random_seed=random_seed, volumes_dir=volumes_dir,
            is_standard_pipeline=False, environment=runtime_environment,
        )

        result = runtime.fit(inputs, return_values=['outputs.0'])
        result.check_success()

        output = result.values['outputs.0']

        if not isinstance(output, container.DataFrame):
            raise TypeError(
                "A standard pipeline's output should be of a container DataFrame type, not {output_type}.".format(
                    output_type=type(output),
                ))

        # add dataset information
        for input_value in inputs:
            result.pipeline_run.add_input_dataset(input_value)

        return runtime, output, result.pipeline_run

