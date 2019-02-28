from experimenter import Experimenter


def test_main():
    datasets_dir = '/datasets/'
    volumes_dir = '/volumes'
    pipeline_path = './pipe.yml'
    meta_file_path = './.meta'
    seed_problem_directory = ['/seed_datasets_current/']
    classifiers = ['d3m.primitives.sklearn_wrap.SKGaussianNB']
    preprocessors = []  # give no preprocessors

    seed_classification_problems = ['/datasets//seed_datasets_current/4550_MiceProtein',
                               '/datasets//seed_datasets_current/1491_one_hundred_plants_margin',
                               '/datasets//seed_datasets_current/LL1_726_TIDY_GPS_carpool_bus_service_rating_prediction',
                               '/datasets//seed_datasets_current/LL0_1100_popularkids',
                               '/datasets//seed_datasets_current/LL0_acled_reduced',
                               '/datasets//seed_datasets_current/313_spectrometer',
                               '/datasets//seed_datasets_current/uu4_SPECT',
                               '/datasets//seed_datasets_current/66_chlorineConcentration',
                               '/datasets//seed_datasets_current/LL0_acled',
                               '/datasets//seed_datasets_current/185_baseball',
                               '/datasets//seed_datasets_current/LL0_186_braziltourism',
                               '/datasets//seed_datasets_current/27_wordLevels',
                               '/datasets//seed_datasets_current/1567_poker_hand',
                               '/datasets//seed_datasets_current/38_sick',
                               '/datasets//seed_datasets_current/57_hypothyroid',
                               '/datasets//seed_datasets_current/32_wikiqa']


    num_pipeline_steps = 6  # Denormalize/DatasetToDataFrame/ColumnParser/SKImputer/SKGaussianNB/Construct Predictions
    pipeline_step_zero = 'd3m.primitives.datasets.Denormalize'
    pipeline_step_fifth = 'd3m.primitives.data.ConstructPredictions'

    experimenter_driver = Experimenter(datasets_dir, volumes_dir, pipeline_path, meta_file_path, seed_problem_directory,
                                       classifiers, preprocessors)
    print("Testing whether the problem created are what they should be...")
    assert(experimenter_driver.problems == seed_classification_problems)
    print("Passed! \n")

    print("Testing that the pipelines are what they should be...")
    # should only make one pipeline with no preprocessor
    assert(len(experimenter_driver.generated_pipelines) == 1)
    generated_pipelines = experimenter_driver.generated_pipelines[0].to_json_structure()
    # make sure there are the normal number of steps in the pipeline
    assert(len(generated_pipelines['steps']) == num_pipeline_steps)
    assert(generated_pipelines['steps'][0]['primitive']['python_path'] == pipeline_step_zero)
    assert(generated_pipelines['steps'][5]['primitive']['python_path'] == pipeline_step_fifth)
    print("Passed!")


if __name__ == "__main__":
    test_main()