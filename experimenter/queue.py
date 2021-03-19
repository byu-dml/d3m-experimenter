import typing

import redis
import rq

from experimenter import config, exceptions


_DEFAULT_QUEUE = 'default'
_EMPTIED_MESSAGE = 'queue {} emptied'


def get_connection():
    config.validate_redis_host()
    return redis.StrictRedis(host=config.redis_host)


def is_running():
    try:
        get_connection().ping()
        return True
    except (exceptions.ConfigError, redis.exceptions.ConnectionError):
        return False


def get_queue(queue_name: str = _DEFAULT_QUEUE) -> rq.Queue:
    return rq.Queue(queue_name, connection=get_connection())
    
    
def get_worker_message(workers: list, queue):
    num_workers = len(workers)
    message = 'number of workers on queue {}: {}'.format(queue.name, num_workers)
    for it, worker in enumerate(workers):
        success = worker.successful_job_count
        fail = worker.failed_job_count
        message = message+'\n\t\t\t worker: {}'.format(it)
        message = message+'\n\t\t\t\t number of successful jobs: {}'.format(success)
        message = message+'\n\t\t\t\t number of failed jobs: {}'.format(fail) 
    return message
    

def get_failed_job(queue_name:str = _DEFAULT_QUEUE, job_num:int = 0):
    #pass name and connection
    reg = rq.registry.FailedJobRegistry(name = queue_name, connection = get_connection())
    job_ids = reg.get_job_ids()
    if (len(job_ids)<=0):
        return "None", reg
    job = job_ids[0]
    job = rq.job.Job.fetch(job, connection=get_connection())
    return job.exc_info, reg
    
    
def save_failed_job(queue_name:str = _DEFAULT_QUEUE, job_num:int = 0):
    if (queue_name is None):
        queue_name = _DEFAULT_QUEUE
    with open (os.path.join('/data',"failed_job_{}.txt".format(job_num)), 'w') as job_file:
        job_file.write(get_failed_job(queue_name=queue_name, job_num=job_num)[0])


def get_queue_message(queues: list):
    queues_message = 'getting queues, jobs, and workers'
    for queue in queues:
        queues_message = queues_message + '\n\t number of jobs on queue {}: {}'.format(queue.name, len(queue))
        _, reg = get_failed_job(queue.name)
        num_fails = len(reg)
        queues_message = queues_message + '\n\t number of failed jobs on queue {}: {}'.format(queue.name, num_fails)
        workers = rq.Worker.all(queue=queue)
        queues_message = queues_message + '\n\t\t' + str(get_worker_message(workers=workers, queue=queue))
        
    return queues_message


def status() -> None:
    conn = get_connection()
    queues = rq.Queue.all(conn)
    queues_message = get_queue_message(queues)
    print('available queues: {}'.format(queues))
    print(queues_message)
    

def enqueue(job, queue_name: str = _DEFAULT_QUEUE, job_timeout: int = None) -> rq.job.Job:
    q = get_queue(queue_name)
    return q.enqueue(**job, job_timeout=job_timeout)


def empty(queue_name: str = None, empty_failed_queue: bool = False) -> None:
    if queue_name is None:
        queue_name = _DEFAULT_QUEUE
    #empty the failed queue or just the normal one    
    if (empty_failed_queue is True):
        empty_failed(queue_name=queue_name)
    else:
        queue = get_queue(queue_name)
        queue.empty()
        print(_EMPTIED_MESSAGE.format(queue_name))


def _check_redis_connection() -> typing.Optional[Exception]:
    error = None
    try:
        get_connection().ping()
    except redis.exceptions.RedisError as e:
        error = e
    return error
    
    
def empty_failed(queue_name: str = None) -> None:
    if queue_name is None:
        queue_name = _DEFAULT_QUEUE
    _, failed_queue = get_failed_job(queue_name=queue_name)
    #loop through the jobs and remove them
    conn = get_connection()
    job_ids = failed_queue.get_job_ids()
    for job_id in job_ids:
        result = failed_queue.remove(job_id, delete_job=True)
    print(_EMPTIED_MESSAGE.format(queue_name+str(' failed')))
        

def make_job(f: typing.Callable, *args: typing.Any, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]:
    return {'f':f, 'args': args, 'kwargs': kwargs}


def enqueue_jobs(
    jobs: typing.Union[typing.Generator, typing.Iterator, typing.Sequence], *,
    job_timeout: int = None, queue_name: str = _DEFAULT_QUEUE,
) -> None:
    """
    Connects to the job queue and enqueues all `jobs`.

    jobs: the jobs to push onto the queue
        Each job must be formatted as a dict with the keys `'f'`, `'args'` (optional), and `'kwargs'` optional.
    """
    if _check_redis_connection() is not None:
        raise exceptions.ServerError(_STATUS_STOPPED_MESSAGE)

    connection = get_connection()
    queue = rq.Queue(queue_name, connection=connection)

    for job in jobs:
        queue.enqueue(**job, job_timeout=job_timeout)
