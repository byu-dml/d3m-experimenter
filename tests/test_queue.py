import contextlib
import io
import itertools
import random
import time
import unittest

from experimenter import exceptions, queue, utils


@unittest.skipIf(queue.is_running(), 'existing queue server detected')
class QueueTestCase(unittest.TestCase):

    @staticmethod
    def _clean_up_queue():
        with utils.redirect_stdout():
            queue.start()
            queue.empty()
            queue.stop()

        if queue.is_running():
            raise exceptions.InvalidStateError(
                'failed to clean up queue server on port {port}'.format(queue._get_redis_port())
            )

    @classmethod
    def tearDownClass(cls):
        cls._clean_up_queue()

    def tearDown(self):
        self._clean_up_queue()

    def test_start_stop_status(self):
        """
        this tests all three methods together because they are inter-related and for efficiency
        """
        self.assertFalse(queue.is_running())

        # stop from stopped
        with utils.redirect_stdout() as buf:
            queue.stop()
            self.assertEqual(buf.getvalue().strip(), queue._QUEUE_STOP_SUCCESS_MESSAGE)

        # status when stopped
        with utils.redirect_stdout() as buf:
            queue.status()
            self.assertEqual(buf.getvalue().strip(), queue._QUEUE_STATUS_STOPPED_MESSAGE)

        # start from stopped
        with utils.redirect_stdout() as buf:
            queue.start()
            self.assertEqual(buf.getvalue().strip(), queue._QUEUE_START_SUCCESS_MESSAGE.format(port=queue._DEFAULT_HOST_PORT))

        self.assertTrue(queue.is_running())

        # status when started
        with utils.redirect_stdout() as buf:
            queue.status()
            self.assertEqual(buf.getvalue().strip(), queue._QUEUE_STATUS_RUNNING_MESSAGE.format(port=queue._get_redis_port()))

        # start from started
        with utils.redirect_stdout() as buf:
            queue.start()
            self.assertEqual(buf.getvalue().strip(), queue._QUEUE_START_SUCCESS_MESSAGE.format(port=queue._DEFAULT_HOST_PORT))

        # stop from started
        with utils.redirect_stdout() as buf:
            queue.stop()
            self.assertEqual(buf.getvalue().strip(), queue._QUEUE_STOP_SUCCESS_MESSAGE)

        self.assertFalse(queue.is_running())

    def test_make_job(self):
        with self.assertRaises(TypeError) as ctx:
            queue.make_job()

        def add(*args, **kwargs):
            return sum(args) + sum(kwargs.values())

        self.assertEqual(queue.make_job(add), {'f': add, 'args': (), 'kwargs': {}})

        self.assertEqual(queue.make_job(add, 3), {'f': add, 'args': (3,), 'kwargs': {}})

        self.assertEqual(queue.make_job(add, c=1), {'f': add, 'args': (), 'kwargs': {'c':1}})

        self.assertEqual(queue.make_job(add, 3, c=1), {'f': add, 'args': (3,), 'kwargs': {'c':1}})

    def test_enqueue_jobs(self):
        with utils.redirect_stdout():
            queue.start()

        hosts = [None, 'localhost']
        ports = [None, queue._DEFAULT_HOST_PORT]
        timeouts = [None, 10]
        f = time.sleep

        for host, port, timeout in itertools.product(hosts, ports, timeouts):
            jobs = (
                queue.make_job(f),
                queue.make_job(f, 1),
                queue.make_job(f, secs=1),
            )
            queue.enqueue_jobs(jobs, queue_host=host, queue_port=port, job_timeout=timeout)

        with utils.redirect_stdout():
            queue.empty()
            queue.stop()

    def test_enqueue_jobs_stopped_queue(self):
        f = time.sleep
        generator = (
            queue.make_job(f, 1),
            queue.make_job(f, secs=1),
        )
        with self.assertRaises(exceptions.ServerError):
            queue.enqueue_jobs(generator)

    def test_start_worker(self):
        with utils.redirect_stdout():
            queue.start()

        queue.start_worker()

        with utils.redirect_stdout():
            queue.stop()

if __name__ == '__main__':
    unittest.main()
