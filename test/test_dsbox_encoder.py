import unittest
from typing import Dict, List

import pandas as pd
from d3m.container.pandas import DataFrame
from d3m.metadata import base as metadata_base

from experimenter.config import d3m_index


class DSBOXEncoderTestCase(unittest.TestCase):

    def setUp(self):
        self.Encoder = d3m_index.get_primitive('d3m.primitives.data_preprocessing.dsbox_encoder.BYU')
        self.hyperparams_class = self.Encoder.metadata.query()['primitive_code']['class_type_arguments']['Hyperparams']
        self.semantics = {
            "categorical": "https://metadata.datadrivendiscovery.org/types/CategoricalData",
            "ordinal": "https://metadata.datadrivendiscovery.org/types/OrdinalData",
            "attribute": "https://metadata.datadrivendiscovery.org/types/Attribute"
        }

        self.categorical_data = self._make_df(
            ["cat", "num"],
            [
                [1, 3.4],
                [1, 4.5],
                [2, 1.1],
                [1, 8.2]
            ],
            [
                [self.semantics['attribute'], self.semantics['categorical']],
                [self.semantics['attribute']]
            ]
        )
        self.categorical_data2 = self._make_df(
            ["cat", "num"],
            [
                [1, 7.4],
                [3, 1.5],
                [2, 3.1],
                [1, 5.2]
            ],
            [
                [self.semantics['attribute'], self.semantics['categorical']],
                [self.semantics['attribute']]
            ]
        )
        self.ordinal_data = self._make_df(
            ["ord", "num"],
            [
                [1, 3.4],
                [1, 4.5],
                [2, 1.1],
                [1, 8.2]
            ],
            [
                [self.semantics['attribute'], self.semantics['ordinal']],
                [self.semantics['attribute']]
            ]
        )
        self.numeric_data = self._make_df(
            ["intcol", "floatcol"],
            [
                [1, 3.4],
                [1, 4.5],
                [2, 1.1],
                [1, 8.2]
            ],
            [
                [self.semantics['attribute']],
                [self.semantics['attribute']]
            ]
        )
    
    def test_can_encode_categorical(self):
        """
        Ensures categorical attributes are encoded.
        """
        after_onehot = self._fit_produce(self.categorical_data)

        self.assertEqual(after_onehot.shape, (4, 4))
        self.assertEqual(after_onehot['cat_1'].sum(), 3)
        self.assertEqual(after_onehot['cat_2'].sum(), 1)
    
    def test_can_encode_ordinal(self):
        """
        Ensures ordinal attributes are encoded.
        """
        after_onehot = self._fit_produce(self.ordinal_data)

        self.assertEqual(after_onehot.shape, (4, 4))
        self.assertEqual(after_onehot['ord_1'].sum(), 3)
        self.assertEqual(after_onehot['ord_2'].sum(), 1)
    
    def test_wont_encode_non_categorical(self):
        """
        Ensures only attributes that are ordinal or categorical
        are encoded.
        """
        after_onehot = self._fit_produce(self.numeric_data)
        self.assertEqual(after_onehot.shape, (4,2))
        self.assertTrue(
            self._are_lists_equal(after_onehot.columns, ['intcol', 'floatcol'])
        )
    
    def test_can_handle_unseen_values(self):
        """
        Ensures the primitive does not break when produced on data
        that has values the primitive did not see while it was
        fitting.
        """
        one_hotter = self._fit(self.categorical_data)
        after_onehot = one_hotter.produce(inputs=self.categorical_data2).value

        self.assertEqual(after_onehot.shape, (4, 4))
        self.assertEqual(after_onehot['cat_1'].sum(), 2)
        self.assertEqual(after_onehot['cat_2'].sum(), 1)
    
    def _are_lists_equal(self, l1, l2) -> bool:
        if len(l1) != len(l2):
            return False
        return all(a == b for a, b in zip(l1, l2))
    
    def _fit(self, df: DataFrame):
        one_hotter = self.Encoder(hyperparams=self.hyperparams_class.defaults())
        one_hotter.set_training_data(inputs=df)
        one_hotter.fit()
        return one_hotter
    
    def _fit_produce(self, df: DataFrame) -> DataFrame:
        one_hotter = self.Encoder(hyperparams=self.hyperparams_class.defaults())
        one_hotter.set_training_data(inputs=df)
        one_hotter.fit()
        return one_hotter.produce(inputs=df).value
    
    def _make_df(
        self,
        col_names: List[str],
        data: list,
        semantic_types: List[List[str]]
    ) -> DataFrame:
        # Make the data
        df: DataFrame = DataFrame(
            pd.DataFrame(data, columns=col_names),
            generate_metadata=True
        )
        # Add each column's semantic types
        for col_i in range(df.shape[1]):
            col_semantic_types = semantic_types[col_i]
            for semantic_type in col_semantic_types:
                df.metadata = df.metadata.add_semantic_type(
                    (metadata_base.ALL_ELEMENTS, col_i),
                    semantic_type
                )
        return df

    def _print_metadata(self, df: DataFrame, name: str) -> None:
        print(f'\n"{name}" Data Frame:')
        print(df)
        print('column metadata:')
        for col_i in range(df.shape[1]):
            print(df.metadata.query_column(col_i))
