import unittest

from experimenter import d3m_db, download as download_module


# TODO: add local database
@unittest.skipIf(not d3m_db.ping(), 'could not connect to D3M Metalearning Database')
class DownloadTestCase(unittest.TestCase):

    def test_generate_download_jobs(self):
        for index in ['pipelines', 'pipeline_runs']:
            try:
                job = next(download_module.generate_download_jobs(index, 10000, 10))
            except StopIteration:
                self.fail('failed to generate jobs from index: {}'.format(index))
            self.assertEqual(job['f'], download_module.download)


if __name__ == '__main__':
    unittest.main()
