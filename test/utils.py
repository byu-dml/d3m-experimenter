from test.config import test_problem_reference, ProblemReference
from experimenter.pipeline_builder import EZPipeline
from experimenter.run_pipeline import RunPipeline


def run_experimenter_from_pipeline(
    pipeline_to_run: EZPipeline,
    arch_type: str = "",
    volumes_dir: str = "/volumes",
    problem: ProblemReference = test_problem_reference,
):
    # run our system
    run_pipeline = RunPipeline(volumes_dir=volumes_dir, problem_path=problem.path)
    scores_test, _ = run_pipeline.run(pipeline=pipeline_to_run)
    # the value of score is in the first document in the first index
    score = scores_test[0]["value"][0]
    print(f"score for {arch_type} pipeline: {score}")
    return score
