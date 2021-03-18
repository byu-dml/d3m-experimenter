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
            queue.make_job(time.sleep, 0.001),
            queue.make_job(queue.make_job, queue.make_job, 1, 2, 3),
            queue.make_job(time.sleep, 0.001)
        ]

        queued_jobs = [queue.enqueue(job) for job in jobs]

        utils.wait(lambda: queued_jobs[-1].get_status() != 'queued', 0.1, 0.01)

        for job in queued_jobs:
            self.assertEqual(job.get_status(), 'finished')


if __name__ == '__main__':
    unittest.main()
