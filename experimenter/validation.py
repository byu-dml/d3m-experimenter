import logging
import typing as t

from d3m.metadata.pipeline_run import (
    validate_pipeline_run as d3m_validate_pipeline_run,
    validate_pipeline as d3m_validate_pipeline,
    validate_problem as d3m_validate_problem,
    validate_dataset as d3m_validate_dataset,
)

logger = logging.getLogger(__name__)


def validate_pipeline_run(pipeline_run: dict) -> bool:
    return _wrap_validator(d3m_validate_pipeline_run, pipeline_run, "pipeline run")


def validate_pipeline(pipeline_description: dict) -> bool:
    return _wrap_validator(d3m_validate_pipeline, pipeline_description, "pipeline")


def validate_problem(problem_description: dict) -> bool:
    return _wrap_validator(d3m_validate_problem, problem_description, "problem")


def validate_dataset(dataset_description: dict) -> bool:
    return _wrap_validator(d3m_validate_dataset, dataset_description, "dataset")


def _wrap_validator(validator: t.Callable, entity: dict, name: str) -> bool:
    """
    Wraps a D3M validator function to return a True/False indicator of passing
    the validation, rather than raising an exception on failed validation.
    """
    try:
        validator(entity)
        return True
    except Exception as e:
        logger.warning(f"{name} invalid, details:")
        logger.warning(e)
        return False
