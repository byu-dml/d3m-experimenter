import itertools
import unittest

from parameterized import parameterized

from experimenter import d3m_db


@unittest.skipIf(not d3m_db.ping(), 'could not connect to D3M Metalearning Database')
class D3M_DBTestCase(unittest.TestCase):

    def test_get_index_timestamp_range(self):
        d3m_db.get_index_timestamp_range('datasets')
        d3m_db.get_index_timestamp_range('datasets', False)
        d3m_db.get_index_timestamp_range('problems', True)

    # timestamps known to work on March 26, 2021
    @parameterized.expand(itertools.product(
        ['datasets', 'problems'],
        [None, '2019-06-20T14:33:01.347Z'],
        [None, '2021-01-28T13:27:07.942Z'],
        [False, True],
        [False, True],
    ))
    def test_count(self, index, start, end, start_inclusive, end_inclusive):
        count = d3m_db.count(index, start, end, start_inclusive, end_inclusive)
        self.assertTrue(count > 0)

    def test_count_all_indexes(self):
        for index in d3m_db.D3M_INDEXES:
            count = d3m_db.count(index)
            self.assertTrue(count > 0)


if __name__ == '__main__':
    unittest.main()
