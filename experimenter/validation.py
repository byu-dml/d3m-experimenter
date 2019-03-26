import typing

from d3m import exceptions

from d3m.utils import load_schema_validators
from d3m.metadata import base as metadata_base
import jsonschema


SUCCESS = metadata_base.PipelineRunStatusState.SUCCESS.name
FAILURE = metadata_base.PipelineRunStatusState.FAILURE.name


def validate_pipeline_run(new_pipeline_json):
    PIPELINE_RUN_SCHEMA_VALIDATOR, = load_schema_validators(metadata_base.SCHEMAS, ('pipeline_run.json',))
    try:
        PIPELINE_RUN_SCHEMA_VALIDATOR.validate(new_pipeline_json)
        _validate_pipeline_run_status_consistency(new_pipeline_json)
        return True
    except Exception as error:
        print('\n', error, '\n')
        return False


def _validate_pipeline_run_status_consistency(
        json_structure: typing.Dict
) -> None:
    """
    Verifies that the success or failure states of pipeline_run components are consistent with
    each other. A pipeline_run (or subpipeline) is successful if and only if all steps and
    method_calls are successful. All status states should indicate a success. A failed
    pipeline_run (or subpipeline) occurs when a method_call failed. This failure state should
    be propagated upwards to all parent steps and pipeline_run. The runtime should
    "short-circuit" and there should only be one failed method_call.
    """

    def check_success_step(step):
        if step['type'] == metadata_base.PipelineStepType.PRIMITIVE.name:
            for method_call in step['method_calls']:
                if SUCCESS != method_call['status']['state']:
                    raise Exception(
                        'Step with "{}" status has method_call with "{}" status'.format(
                            SUCCESS, FAILURE
                        )
                    )
        elif step['type'] == metadata_base.PipelineStepType.SUBPIPELINE.name:
            recurse_success(step)
        else:
            raise exceptions.InvalidArgumentValueError(
                'Invalid pipeline_run or subpipeline step'
            )

    def check_failure_step(step):
        if step['type'] == 'PRIMITIVE':
            found_a_method_call_failure = False
            for method_call in step['method_calls']:
                if found_a_method_call_failure:
                    raise Exception(
                        'More than one method_call with \'FAILURE\' status found'
                    )
                if method_call['status']['state'] == FAILURE:
                    found_a_method_call_failure = True
        elif step['type'] == 'SUBPIPELINE':
            recurse_failure(step)
        else:
            raise exceptions.InvalidArgumentValueError(
                'Invalid pipeline_run or subpipeline step'
            )

    def recurse_success(json_structure):
        for step in json_structure['steps']:
            if SUCCESS != step['status']['state']:
                raise Exception(
                    'Pipeline_run or subpipeline_step with "{}" status has a step with "{}" ' \
                    'status'.format(SUCCESS, FAILURE)
                )
            check_success_step(step)

    def recurse_failure(json_structure):
        found_a_step_failure = False
        # a step is successful iff all method_calls(PRIMITIVE) or steps(SUBPIPELINE) are successful
        for step in json_structure['steps']:
            if found_a_step_failure:
                raise Exception(
                    'More than one step with \'FAILURE\' status found'
                )
            if step['status']['state'] == SUCCESS:
                check_success_step(step)
            # a step fails iff at least one method_call(PRIMITIVE) or step(SUBPIPELINE) fails
            elif step['status']['state'] == FAILURE:
                found_a_step_failure = True
                check_failure_step(step)

    state = json_structure['status']['state']
    if state == SUCCESS:
        recurse_success(json_structure)
    elif state == FAILURE:
        recurse_failure(json_structure)
    else:
        raise exceptions.InvalidArgumentValueError(
            'Invalid pipeline_run state: {}'.format(state)
        )