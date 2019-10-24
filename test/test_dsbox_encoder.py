import unittest

import pandas as pd
from d3m.container.pandas import DataFrame
from d3m import index as d3m_index
from d3m.metadata import base as metadata_base


class PipelineGenerationTestCase(unittest.TestCase):

    OneHotter = d3m_index.get_primitive('d3m.primitives.data_preprocessing.encoder.DSBOX')

    def print_metadata(df: DataFrame, name: str) -> None:
        print(f'\n"{name}" Data Frame:')
        print(df)
        print('column metadata:')
        for col_i in range(df.shape[1]):
            print(df.metadata.query_column(col_i))

    df: DataFrame = DataFrame(pd.DataFrame({
        "A": [1, 2, 1, 1],
        "B": [1.9, 2.5, 10, 4.3]
    }), generate_metadata=True)
    df.metadata = df.metadata.add_semantic_type((metadata_base.ALL_ELEMENTS, 0), "https://metadata.datadrivendiscovery.org/types/CategoricalData")
    df.metadata = df.metadata.add_semantic_type((metadata_base.ALL_ELEMENTS, 0), "https://metadata.datadrivendiscovery.org/types/Attribute")
    df.metadata = df.metadata.add_semantic_type((metadata_base.ALL_ELEMENTS, 1), "https://metadata.datadrivendiscovery.org/types/Attribute")

    df_test: DataFrame = DataFrame(pd.DataFrame({
        "A": [1, 2, 2, 3],
        "B": [3.4, 5.6, 1.2, 3.7]
    }), generate_metadata=True)
    df_test.metadata = df_test.metadata.add_semantic_type((metadata_base.ALL_ELEMENTS, 0), "https://metadata.datadrivendiscovery.org/types/CategoricalData")
    df_test.metadata = df_test.metadata.add_semantic_type((metadata_base.ALL_ELEMENTS, 0), "https://metadata.datadrivendiscovery.org/types/Attribute")
    df_test.metadata = df_test.metadata.add_semantic_type((metadata_base.ALL_ELEMENTS, 1), "https://metadata.datadrivendiscovery.org/types/Attribute")

    print_metadata(df, 'df')
    print_metadata(df_test, 'test df')

    hyperparams_class = OneHotter.metadata.query()['primitive_code']['class_type_arguments']['Hyperparams']
    one_hotter = OneHotter(hyperparams=hyperparams_class.defaults())

    one_hotter.set_training_data(inputs=df)
    one_hotter.fit()
    print('one hotter mapping:')
    print(f'mapping={one_hotter._mapping}, cat columns={one_hotter._cat_columns}')
    after_onehot = one_hotter.produce(inputs=df).value
    print_metadata(after_onehot, 'after_onehot')

    test_after_onehot = one_hotter.produce(inputs=df_test).value
    print_metadata(test_after_onehot, 'test_after_onehot')

