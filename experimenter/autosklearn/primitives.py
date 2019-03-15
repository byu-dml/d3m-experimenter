from collections import OrderedDict
import pickle
import sys

from sklearn.preprocessing import LabelEncoder

from autosklearn.classification import AutoSklearnClassifier
from d3m import container
from d3m.metadata import base as metadata_base, hyperparams, params
from d3m.primitive_interfaces.base import CallResult
from d3m.primitive_interfaces.supervised_learning import SupervisedLearnerPrimitiveBase


__all__ = ('AutoSklearnClassifierPrimitive',)


Inputs = container.DataFrame
Outputs = container.DataFrame


# class Params(params.Params):

#     classifier: AutoSklearnClassifier


class Hyperparams(hyperparams.Hyperparams):

    time_left_for_this_task = hyperparams.UniformInt(
        lower=1,
        upper=sys.maxsize,
        default=20,
        description='Time limit in seconds for the search of appropriate models. By increasing this value, auto-sklearn has a higher chance of finding better models.',
        semantic_types=[
            'https://metadata.datadrivendiscovery.org/types/ResourcesUseParameter',
            'https://metadata.datadrivendiscovery.org/types/TuningParameter',
        ],
    )
    
    per_run_time_limit = hyperparams.UniformInt(
        lower=1,
        upper=sys.maxsize,
        default=5,
        description='Time limit for a single call to the machine learning model. Model fitting will be terminated if the machine learning algorithm runs over the time limit. Set this value high enough so that typical machine learning algorithms can be fit on the training data.',
        semantic_types=[
            'https://metadata.datadrivendiscovery.org/types/ResourcesUseParameter',
            'https://metadata.datadrivendiscovery.org/types/TuningParameter',
        ],
    )

    initial_configurations_via_metalearning = hyperparams.UniformInt(
        lower=1,
        upper=sys.maxsize,
        default=25,
        description='Initialize the hyperparameter optimization algorithm with this many configurations which worked well on previously seen datasets. Disable if the hyperparameter optimization algorithm should start from scratch.',
        semantic_types=[
            'https://metadata.datadrivendiscovery.org/types/ControlParameter',
            'https://metadata.datadrivendiscovery.org/types/TuningParameter',
        ],
    )

    ensemble_size = hyperparams.UniformInt(
        lower=1,
        upper=sys.maxsize,
        default=50,
        description='Number of models added to the ensemble built by Ensemble selection from libraries of models. Models are drawn with replacement.',
        semantic_types=[
            'https://metadata.datadrivendiscovery.org/types/ControlParameter',
            'https://metadata.datadrivendiscovery.org/types/TuningParameter',
        ],
    )
    
    ensemble_nbest = hyperparams.UniformInt(
        lower=1,
        upper=sys.maxsize,
        default=50,
        description='Only consider the ensemble_nbest models when building an ensemble. Implements Model Library Pruning from Getting the most out of ensemble selection.',
        semantic_types=[
            'https://metadata.datadrivendiscovery.org/types/ControlParameter',
            'https://metadata.datadrivendiscovery.org/types/TuningParameter',
        ],
    )

    ensemble_memory_limit = hyperparams.UniformInt(
        lower=1,
        upper=sys.maxsize,
        default=1024,
        description='Memory limit in MB for the ensemble building process. auto-sklearn will reduce the number of considered models (ensemble_nbest) if the memory limit is reached.',
        semantic_types=[
            'https://metadata.datadrivendiscovery.org/types/ResourcesUseParameter',
        ],
    )

    ml_memory_limit = hyperparams.UniformInt(
        lower=1,
        upper=sys.maxsize,
        default=3072,
        description='Memory limit in MB for the machine learning algorithm. auto-sklearn will stop fitting the machine learning algorithm if it tries to allocate more than ml_memory_limit MB.',
        semantic_types=[
            'https://metadata.datadrivendiscovery.org/types/ResourcesUseParameter',
        ],
    )

    # TODO
    # include_estimators : list, optional (None)
    # If None, all possible estimators are used. Otherwise specifies set of estimators to use.

    # exclude_estimators : list, optional (None)
    # If None, all possible estimators are used. Otherwise specifies set of estimators not to use. Incompatible with include_estimators.

    # include_preprocessors : list, optional (None)
    # If None all possible preprocessors are used. Otherwise specifies set of preprocessors to use.

    # exclude_preprocessors : list, optional (None)
    # If None all possible preprocessors are used. Otherwise specifies set of preprocessors not to use. Incompatible with include_preprocessors.

    # resampling_strategy : string or object, optional (‘holdout’)
    # how to to handle overfitting, might need ‘resampling_strategy_arguments’

    # ‘holdout’: 67:33 (train:test) split
    # ‘holdout-iterative-fit’: 67:33 (train:test) split, calls iterative fit where possible
    # ‘cv’: crossvalidation, requires ‘folds’
    # ‘partial-cv’: crossvalidation with intensification, requires ‘folds’
    # BaseCrossValidator object: any BaseCrossValidator class found
    # in scikit-learn model_selection module
    # _RepeatedSplits object: any _RepeatedSplits class found
    # in scikit-learn model_selection module
    # BaseShuffleSplit object: any BaseShuffleSplit class found
    # in scikit-learn model_selection module
    # resampling_strategy_arguments : dict, optional if ‘holdout’ (train_size default=0.67)
    # Additional arguments for resampling_strategy:

    # train_size should be between 0.0 and 1.0 and represent the proportion of the dataset to include in the train split.
    # shuffle determines whether the data is shuffled prior to splitting it into train and validation.
    # Available arguments:

    # ‘holdout’: {‘train_size’: float}
    # ‘holdout-iterative-fit’: {‘train_size’: float}
    # ‘cv’: {‘folds’: int}
    # ‘partial-cv’: {‘folds’: int, ‘shuffle’: bool}
    # BaseCrossValidator or _RepeatedSplits or BaseShuffleSplit object: all arguments
    # required by chosen class as specified in scikit-learn documentation. If arguments are not provided, scikit-learn defaults are used. If no defaults are available, an exception is raised. Refer to the ‘n_splits’ argument as ‘folds’.
    # tmp_folder : string, optional (None)
    # folder to store configuration output and log files, if None automatically use /tmp/autosklearn_tmp_$pid_$random_number

    # output_folder : string, optional (None)
    # folder to store predictions for optional test set, if None automatically use /tmp/autosklearn_output_$pid_$random_number

    # delete_tmp_folder_after_terminate: string, optional (True)
    # remove tmp_folder, when finished. If tmp_folder is None tmp_dir will always be deleted

    # delete_output_folder_after_terminate: bool, optional (True)
    # remove output_folder, when finished. If output_folder is None output_dir will always be deleted

    # shared_mode : bool, optional (False)
    # Run smac in shared-model-node. This only works if arguments tmp_folder and output_folder are given and both delete_tmp_folder_after_terminate and delete_output_folder_after_terminate are set to False. Cannot be used together with n_jobs.

    # n_jobs : int, optional, experimental
    # The number of jobs to run in parallel for fit(). Cannot be used together with shared_mode. -1 means using all processors. By default, Auto-sklearn uses a single core for fitting the machine learning model and a single core for fitting an ensemble. Ensemble building is not affected by n_jobs but can be controlled by the number of models in the ensemble. In contrast to most scikit-learn models, n_jobs given in the constructor is not applied to the predict() method.

    # disable_evaluator_output: bool or list, optional (False)
    # If True, disable model and prediction output. Cannot be used together with ensemble building. predict() cannot be used when setting this True. Can also be used as a list to pass more fine-grained information on what to save. Allowed elements in the list are:

    # 'y_optimization' : do not save the predictions for the optimization/validation set, which would later on be used to build an ensemble.
    # 'model' : do not save any model files
    # smac_scenario_args : dict, optional (None)
    # Additional arguments inserted into the scenario of SMAC. See the SMAC documentation for a list of available arguments.

    # get_smac_object_callback : callable
    # Callback function to create an object of class smac.optimizer.smbo.SMBO. The function must accept the arguments scenario_dict, instances, num_params, runhistory, seed and ta. This is an advanced feature. Use only if you are familiar with SMAC.

    # logging_config : dict, optional (None)
    # dictionary object specifying the logger configuration. If None, the default logging.yaml file is used, which can be found in the directory util/logging.yaml relative to the installation.

class AutoSklearnClassifierPrimitive(
    SupervisedLearnerPrimitiveBase[Inputs, Outputs, params.Params, Hyperparams]
):
    """
    A classification ensemble chosen using AutoSKLearn.
    """

    metadata = metadata_base.PrimitiveMetadata({
        'id': 'c3fa1028-8c87-406c-a7d7-d2b840b1973c',
        'version': '0.1.0',
        'name': 'AutoSKLearn Classifier',
        'python_path': 'd3m.primitives.classification.search.AutoSKLearn',
        'keywords': ['AutoSKLearn'],
        'source': {
            'name': 'name',
            'contact': 'mailto:bjschoenfeld@byu.edu',
            'uris': [
                'https://github.com/byu-dml/automl-baselines'
            ]
        },
        'installation': [{
            'type': metadata_base.PrimitiveInstallationType.PIP,
            'package_uri': 'https://github.com/byu-dml/automl-baselines'
        }],
        'algorithm_types': [
            metadata_base.PrimitiveAlgorithmType.ENSEMBLE_LEARNING,
            metadata_base.PrimitiveAlgorithmType.MULTICLASS_CLASSIFICATION,
            metadata_base.PrimitiveAlgorithmType.BINARY_CLASSIFICATION,
        ],
        'primitive_family': metadata_base.PrimitiveFamily.CLASSIFICATION,
    })

    def __init__(
        self, *, hyperparams: Hyperparams, random_seed: int = 0
    ) -> None:
        super().__init__(hyperparams=hyperparams, random_seed=random_seed)
        self._classifier = None
        self._outputs_encoder = None

    def set_training_data(self, *, inputs: Inputs, outputs: Outputs) -> None:
        self._training_inputs = inputs
        self._training_outputs = outputs

    def _init_classifier(self) -> None:
        hyperparams = {'seed': self.random_seed}
        hyperparams.update(self.hyperparams)
        self._classifier = AutoSklearnClassifier(**hyperparams)

    def fit(
        self, *, timeout: float = None, iterations: int = None
    ) -> CallResult[None]:
        if self._training_inputs is None or self._training_outputs is None:
            raise exceptions.InvalidStateError("Missing training data.")

        self._init_classifier()
        encoded_training_outputs = self._fit_outputs_encoder()
        # raise Exception(encoded_training_outputs)
        self._classifier.fit(self._training_inputs, encoded_training_outputs)

        return CallResult(None)

    def _fit_outputs_encoder(self):
        self._outputs_encoder = LabelEncoder()
        return self._outputs_encoder.fit_transform(
            self._training_outputs
        )

    def produce(
        self, *, inputs: Inputs, timeout: float = None, iterations: int = None
    ) -> CallResult[Outputs]:
        if self._classifier is None or self._outputs_encoder is None:
            raise exceptions.InvalidStateError("Primitive not fitted.")

        encoded_predictions = self._classifier.predict(inputs)
        predictions = self._outputs_encoder.inverse_transform(encoded_predictions)

        outputs = container.DataFrame(predictions, generate_metadata=False)

        outputs_metadata = inputs.metadata.clear(for_value=outputs, generate_metadata=True)
        outputs_length = self._training_outputs.metadata.query((metadata_base.ALL_ELEMENTS,))['dimension']['length']
        for column_index in range(outputs_length):
            column_metadata = OrderedDict(outputs_metadata.query_column(column_index))
            outputs_metadata = outputs_metadata.update_column(column_index, column_metadata)

        outputs.columns = self._training_outputs.columns


        return CallResult(outputs)

    def get_params(self) -> None:
        pass
    #     return Params(classifier=pickle.dumps(self._classifier))

    def set_params(self, *, params: params.Params) -> None:
        pass
    #     self._classifier = pickle.loads(params['classifier'])
