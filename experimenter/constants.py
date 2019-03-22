preprocessors = [
    "d3m.primitives.data_preprocessing.standard_scaler.SKlearn",
    "d3m.primitives.feature_selection.generic_univariate_select.SKlearn",
    "d3m.primitives.data_transformation.kernel_pca.SKlearn",
    "d3m.primitives.data_transformation.pca.SKlearn",
    "d3m.primitives.data_transformation.fast_ica.SKlearn",
    "d3m.primitives.feature_selection.select_fwe.SKlearn",
    "d3m.primitives.feature_selection.select_percentile.SKlearn",
    "d3m.primitives.data_preprocessing.min_max_scaler.SKlearn",
    "d3m.primitives.data_preprocessing.nystroem.SKlearn",
]

not_working_preprocessors = [
    # These preprocessors have not been fixed yet by JPL:
    # "d3m.primitives.data_preprocessing.feature_agglomeration.SKlearn",
    # "d3m.primitives.data_preprocessing.rbf_sampler.SKlearn",
    # "d3m.primitives.data_preprocessing.truncated_svd.SKlearn",

    # These preprocessors just don't work and need to be debugged
    # "d3m.primitives.data_preprocessing.polynomial_features.SKlearn",
    # "d3m.primitives.data_transformation.ordinal_encoder.SKlearn",
    # "d3m.primitives.data_transformation.one_hot_encoder.SKlearn",
    # "d3m.primitives.data_preprocessing.rfe.SKlearn",  # Crashes the terminal

]

models = {
    'classification': [
        "d3m.primitives.classification.random_forest.SKlearn",
        "d3m.primitives.classification.gradient_boosting.SKlearn",
        "d3m.primitives.classification.bagging.SKlearn",
        "d3m.primitives.classification.bernoulli_naive_bayes.SKlearn",
        "d3m.primitives.classification.decision_tree.SKlearn",
        "d3m.primitives.classification.gaussian_naive_bayes.SKlearn",
        "d3m.primitives.classification.k_neighbors.SKlearn",
        "d3m.primitives.classification.linear_discriminant_analysis.SKlearn",
        "d3m.primitives.classification.logistic_regression.SKlearn",
        "d3m.primitives.classification.linear_svc.SKlearn",
        "d3m.primitives.classification.sgd.SKlearn",
        "d3m.primitives.classification.svc.SKlearn",
        "d3m.primitives.classification.extra_trees.SKlearn",
        "d3m.primitives.classification.passive_aggressive.SKlearn",
    ],
    'regression': [
        "d3m.primitives.regression.random_forest.SKlearn",
        "d3m.primitives.regression.ard.SKlearn",
        "d3m.primitives.regression.extra_trees.SKlearn",
        "d3m.primitives.regression.decision_tree.SKlearn",
        "d3m.primitives.regression.gaussian_process.SKlearn",
        "d3m.primitives.regression.gradient_boosting.SKlearn",
        "d3m.primitives.regression.k_neighbors.SKlearn",
        "d3m.primitives.regression.lasso_cv.SKlearn",
        "d3m.primitives.regression.svr.SKlearn",
        "d3m.primitives.regression.kernel_ridge.SKlearn",
        "d3m.primitives.regression.lars.SKlearn",
        "d3m.primitives.regression.lasso.SKlearn",
        "d3m.primitives.regression.linear_svr.SKlearn",
        "d3m.primitives.regression.mlp.SKlearn",
        "d3m.primitives.regression.passive_aggressive.SKlearn",
        "d3m.primitives.regression.ridge.SKlearn",
        "d3m.primitives.regression.sgd.SKlearn",
    ]
}
problem_directories = [
    "seed_datasets_current/",
    "training_datasets/LL0/",
    # "training_datasets/LL1/",
]

blacklist_non_tabular_data = [
    "31_urbansound",
    "LL1_3476_HMDB_actio_recognition",
    "uu1_datasmash",
    "30_personae",
    "LL1_crime_chicago",
    "LL0_186_braziltourism",
    "22_handgeometry",
    "uu2_gp_hyperparameter_estimation"
    "uu2_gp_hyperparameter_estimation_v2",
    "LL0_1220_click_prediction_small",
    "LL1_336_MS_Geolife_transport_mode_prediction",  # too long
    "1567_poker_hand",  # too long: ERROR: BSON document too large (19826399 bytes)
    "LL0_1569_poker_hand", # Memory error in NP dot product
    "LL1_336_MS_Geolife_transport_mode_prediction_separate_lat_lon",  # too long
    "LL1_726_TIDY_GPS_carpool_bus_service_rating_prediction", # GPS data in another file
    "66_chlorineConcentration",
    "LL0_1485_madelon",  # too long
    "LL0_1468_cnae_9",  # also too long
]