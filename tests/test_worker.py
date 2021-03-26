import time
import unittest

import rq

from experimenter import queue, utils


@unittest.skipIf(
    not queue.is_running() or len(rq.worker.Worker.all(queue.get_connection())) == 0,
    'queue is not running or there are no workers'
)
class WorkerTestCase(unittest.TestCase):
    # TODO: set a specific queue?

    def test_simple_job(self):
        jobs = [
            utils.format_job(time.sleep, 0.001),
            utils.format_job(utils.format_job, utils.format_job, 1, 2, 3),
            utils.format_job(time.sleep, 0.001)
        ]

        queued_jobs = [queue.enqueue(job) for job in jobs]

        utils.wait(lambda: queued_jobs[-1].get_status() not in ['queued', 'started'], 1.0, 0.01)

        for job in queued_jobs:
            self.assertEqual(job.get_status(), 'finished', job)


if __name__ == '__main__':
    unittest.main()
