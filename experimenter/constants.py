from d3m.metadata.base import ArgumentType

preprocessors = [
    "d3m.primitives.data_preprocessing.standard_scaler.SKlearn",
    "d3m.primitives.feature_selection.generic_univariate_select.SKlearn",
    "d3m.primitives.feature_extraction.kernel_pca.SKlearn",
    "d3m.primitives.feature_extraction.pca.SKlearn",
    "d3m.primitives.feature_selection.select_fwe.SKlearn",
    "d3m.primitives.feature_selection.select_percentile.SKlearn",
    "d3m.primitives.data_preprocessing.min_max_scaler.SKlearn",
    "d3m.primitives.data_preprocessing.nystroem.SKlearn",
    "d3m.primitives.data_preprocessing.quantile_transformer.SKlearn",
    "d3m.primitives.data_preprocessing.random_trees_embedding.SKlearn",
    "d3m.primitives.feature_selection.variance_threshold.SKlearn"
]

not_working_preprocessors = [
    # These preprocessors have not been fixed yet by JPL: TODO: check this, it's old
    # "d3m.primitives.data_preprocessing.feature_agglomeration.SKlearn",
    # "d3m.primitives.data_preprocessing.rbf_sampler.SKlearn",
    # "d3m.primitives.data_preprocessing.truncated_svd.SKlearn",

    # These preprocessors just don't work and need to be debugged
    # "d3m.primitives.data_preprocessing.polynomial_features.SKlearn",
    # "d3m.primitives.data_transformation.ordinal_encoder.SKlearn",
    # "d3m.primitives.data_transformation.one_hot_encoder.SKlearn",
    # "d3m.primitives.data_transformation.fast_ica.SKlearn", # Can't handle a column with all the same values
]

models = {
    'classification': [
        "d3m.primitives.classification.random_forest.SKlearn",
        "d3m.primitives.classification.gradient_boosting.SKlearn",
        "d3m.primitives.classification.bernoulli_naive_bayes.SKlearn",
        "d3m.primitives.classification.decision_tree.SKlearn",
        "d3m.primitives.classification.gaussian_naive_bayes.SKlearn",
        "d3m.primitives.classification.k_neighbors.SKlearn",
        "d3m.primitives.classification.logistic_regression.SKlearn",
        "d3m.primitives.classification.linear_svc.SKlearn",
        "d3m.primitives.classification.sgd.SKlearn",
        "d3m.primitives.classification.svc.SKlearn",
        "d3m.primitives.classification.extra_trees.SKlearn", # randomly splits - different than random forest
        "d3m.primitives.classification.passive_aggressive.SKlearn", # an mlp with regularization
        "d3m.primitives.classification.ada_boost.SKlearn",
        "d3m.primitives.classification.mlp.SKlearn",
        "d3m.primitives.classification.nearest_centroid.SKlearn",
        # "d3m.primitives.classification.multinomial_naive_bayes.SKlearn", # Can't handle negative data
        # "d3m.primitives.classification.linear_discriminant_analysis.SKlearn", # Fails when the values of X are all the same.
        # "d3m.primitives.classification.bagging.SKlearn", # only uses decision trees, which is redudant
    ],
    'regression': [
        # "d3m.primitives.regression.random_forest.SKlearn",
        # "d3m.primitives.regression.ard.SKlearn",
        # "d3m.primitives.regression.extra_trees.SKlearn",
        # "d3m.primitives.regression.decision_tree.SKlearn",
        # "d3m.primitives.regression.gaussian_process.SKlearn",
        # "d3m.primitives.regression.gradient_boosting.SKlearn",
        # "d3m.primitives.regression.k_neighbors.SKlearn",
        # "d3m.primitives.regression.lasso_cv.SKlearn",
        # "d3m.primitives.regression.svr.SKlearn",
        # "d3m.primitives.regression.kernel_ridge.SKlearn",
        # "d3m.primitives.regression.lars.SKlearn",
        # "d3m.primitives.regression.lasso.SKlearn",
        # "d3m.primitives.regression.linear_svr.SKlearn",
        # "d3m.primitives.regression.mlp.SKlearn",
        # "d3m.primitives.regression.passive_aggressive.SKlearn",
        # "d3m.primitives.regression.ridge.SKlearn",
        # "d3m.primitives.regression.sgd.SKlearn",
    ]
}
problem_directories = [
    "seed_datasets_current/",
    "training_datasets/LL0/",
    # "training_datasets/LL1/",
]

EXTRA_HYPEREPARAMETERS = {
    "d3m.primitives.feature_extraction.kernel_pca.SKlearn": [
        {
        "name": "kernel",
            "type": ArgumentType.VALUE,
            "data": "rbf"
        }
    ],
    "d3m.primitives.feature_selection.generic_univariate_select.SKlearn": [
        {
        "name": "mode",
            "type": ArgumentType.VALUE,
            "data": "fpr"
    },
        {
            "name": "param",
            "type": ArgumentType.VALUE,
            "data": 0.05
        }
    ],
}

blacklist_non_tabular_data = [
    "57_hypothyroid"
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
    "LL1_726_TIDY_GPS_carpool_bus_service_rating_prediction",  # GPS data in another file
    "66_chlorineConcentration",
    "LL0_1485_madelon",  # too long
    "LL0_1468_cnae_9",  # also too long
    "LL0_155_pokerhand", # too long
    "LL0_300_isolet",  # too long
    "LL0_312_scene",   # too long
    "LL0_1113_kddcup99",  # too long
    "LL0_180_covertype",   # too long
    "LL0_1122_ap_breast_prostate",  # too long
    "LL0_180_covertype",  # too long
    "LL0_4541_diabetes130us",  # calculation too big, memory error np.dot()
    "LL0_1457_amazon_commerce_reviews",  # timeouts
    "LL0_1176_internet_advertisements",  # timeouts
    "LL0_1036_sylva_agnostic",  # timeouts
    "LL0_1041_gina_prior2",  # timeouts
    "LL0_1501_semeion",  # timeouts
    "LL0_1038_gina_agnostic",  # timeouts
    "LL0_23397_comet_mc_sample",  # timeouts
    "LL0_1040_sylva_prior",  # same for the rest
    "LL0_1476_gas_drift",
    "LL0_4541_diabetes130us",
    "LL0_12_mfeat_factors",
    "LL0_1515_micro_mass",
    "LL0_1219_click_prediction_small",
    "LL0_4134_bioresponse",
    "LL0_1481_kr_vs_k",
    "LL0_1046_mozilla4",
    "LL0_1471_eeg_eye_state",
    "uu3_world_development_indicators",
    "LL0_344_mv",
    "LL0_574_house_16h",
    "LL0_296_ailerons",
    "LL0_216_elevators",
    "LL0_201_pol",
    "uu2_gp_hyperparameter_estimation_v2",  # has extra data
    "uu2_gp_hyperparameter_estimation",  # has extra data
    "57_hypothyroid",  # always NAN's out
    "LL0_315_us_crime",  # the next are due to timeouts
    "LL0_688_visualizing_soil",
    "LL0_189_kin8nm",
    "LL0_572_bank8fm",
    "LL0_308_puma32h"

]