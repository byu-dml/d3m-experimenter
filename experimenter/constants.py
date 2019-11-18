import os

from d3m.metadata.base import ArgumentType, PrimitiveFamily
from d3m import utils as d3m_utils


PACKAGE_NAME = "d3m-experimenter"
REPOSITORY = "https://github.com/byu-dml/d3m-experimenter"
TAG_NAME = d3m_utils.current_git_commit(os.path.dirname(__file__))
D3M_PERFORMER_TEAM = "byu-dml"

# It is ok to use these temperamental preprocessors in production because
# we're ok with some pipelines degenerating on some datasets.
temperamental_preprocessors = [
    # Note: These primitives return an empty DF when the data doesn't
    # have enough signal:
    "d3m.primitives.feature_selection.select_fwe.SKlearn",
    "d3m.primitives.feature_selection.generic_univariate_select.SKlearn",
    "d3m.primitives.feature_selection.select_percentile.SKlearn",
    "d3m.primitives.feature_selection.variance_threshold.SKlearn",
    "d3m.primitives.feature_extraction.kernel_pca.SKlearn",
    # Note: These primitives return an empty DF when the data doesn't
    # have enough signal and only has one column:
    "d3m.primitives.data_preprocessing.quantile_transformer.SKlearn",
]

# These preprocessors never throw errors due to degenerate data
# (i.e. data with no signal). 
bulletproof_preprocessors = [
    "d3m.primitives.data_preprocessing.standard_scaler.SKlearn",
    "d3m.primitives.feature_extraction.pca.SKlearn",
    "d3m.primitives.data_preprocessing.min_max_scaler.SKlearn",
    "d3m.primitives.data_preprocessing.nystroem.SKlearn",
    "d3m.primitives.data_preprocessing.random_trees_embedding.SKlearn",
]

# All useable preprocessors. Use these in production.
preprocessors = temperamental_preprocessors + bulletproof_preprocessors

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

# All primitives that need more than one column as input
primitives_needing_gt_one_column = {
    "d3m.primitives.feature_selection.select_percentile.SKlearn"
}

problem_directories = [
    "seed_datasets_current/",
    "training_datasets/LL0/",
    # Contains mostly non-tabular or huge tabular datasets
    # "training_datasets/LL1/",
]

# This is the full list of families:
# https://metadata.datadrivendiscovery.org/schemas/v0/definitions.json#/definitions/primitive_family
PRIMITIVE_FAMILIES = {
    "classification": [
        PrimitiveFamily.CLASSIFICATION,
        PrimitiveFamily.SEMISUPERVISED_CLASSIFICATION,
        PrimitiveFamily.TIME_SERIES_CLASSIFICATION,
        PrimitiveFamily.VERTEX_CLASSIFICATION
    ]
}

EXTRA_HYPEREPARAMETERS = {
    "d3m.primitives.feature_extraction.kernel_pca.SKlearn": [
        {
            "name": "kernel",
            "argument_type": ArgumentType.VALUE,
            "data": "rbf"
        }
    ],
    "d3m.primitives.feature_selection.generic_univariate_select.SKlearn": [
        {
            "name": "mode",
            "argument_type": ArgumentType.VALUE,
            "data": "fpr"
        },
        {
            "name": "param",
            "argument_type": ArgumentType.VALUE,
            "data": 0.05
        }
    ],
}

blacklist_non_tabular_data = [
    "LL1_ArrowHead", # time series data
    "LL1_TXT_CLS_3746_newsgroup", # requires reading a text file from csv
    "uu_101_object_categories", # requires reading an image file from csv
    "57_hypothyroid",
    "uu10_posts_3", # missing DataSplits file
    "LL1_OSULeaf", # requires reading a text file from csv
    "LL1_FaceFour", # requires reading a text file from csv
    "31_urbansound",
    "LL1_multilearn_emotions" # weird indexes
    "124_174_cifar10", # images
    "124_214_coil20", # images
    "LL1_Haptics", # multiple files
    "LL1_VID_UCF11", # music files
    "LL1_Cricket_Y", # multi file 
    "LL1_ElectricDevices",  # multi file
    "LL1_3476_HMDB_actio_recognition",
    "124_188_usps", # image data
    "uu1_datasmash",
    "LL1_50words", # multi-file
    "30_personae",
    "LL1_crime_chicago",
    "LL1_HandOutlines", # multi file
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
