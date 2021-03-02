import argparse
import typing

from experimenter.modify_generator import ModifyGenerator
from experimenter import config, dashboard, exceptions, queue


def main(argv: typing.Sequence) -> None:
    parser = argparse.ArgumentParser(prog='experimenter')
    configure_parser(parser)
    arguments = parser.parse_args(argv[1:])
    handler(arguments, parser)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '-c', '--config', type=str, default=None, dest='config_path', action='store',
        help='path to the config file',
    )

    subparsers = parser.add_subparsers(dest='experimenter_command')
    subparsers.required = True  # type: ignore

    queue_parser = subparsers.add_parser(
        'queue',
        help='control the job queue',
    )
    configure_queue_parser(queue_parser)

    dashboard_parser = subparsers.add_parser(
        'dashboard',
        help='control the dashboard of the job queue',
    )
    configure_dashboard_parser(dashboard_parser)

    generator_parser = subparsers.add_parser(
        'generator',
        help='generates new pipelines and queues them to run on available datasets',
    )
    configure_generator_parser(generator_parser)

    worker_parser = subparsers.add_parser(
        'worker',
        help='creates a worker to run jobs on pushed onto the queue by a generator',
    )
    configure_worker_parser(worker_parser)


def handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    config.Config(arguments.config_path)  # initializes config singleton

    experimenter_command = arguments.experimenter_command
    subparser = parser._subparsers._group_actions[0].choices[experimenter_command]  # type: ignore

    if experimenter_command == 'queue':
        queue_handler(arguments, subparser)
    elif experimenter_command == 'dashboard':
        dashboard_handler(arguments, subparser)
    elif experimenter_command == 'generator':
        generator_handler(arguments, subparser)
    elif experimenter_command == 'worker':
        worker_handler(arguments, subparser)
    else:
        raise exceptions.InvalidStateError('Unknown experimenter command: {}'.format(experimenter_command))


def configure_queue_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest='queue_command')
    subparsers.required = True  # type: ignore

    start_parser = subparsers.add_parser('start', help='start the queue server')

    stop_parser = subparsers.add_parser('stop', help='stop the queue server')

    status_parser = subparsers.add_parser('status', help='get queue status (started or stopped)')

    empty_parser = subparsers.add_parser('empty', help='remove all jobs from the queue')


def queue_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    queue_command = arguments.queue_command

    if queue_command == 'start':
        queue.start()
    elif queue_command == 'stop':
        queue.stop()
    elif queue_command == 'status':
        queue.status()
    elif queue_command == 'empty':
        queue.empty()
    else:
        raise exceptions.InvalidStateError('Unknown queue command: {}'.format(queue_command))


def configure_dashboard_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest='dashboard_command')
    subparsers.required = True  # type: ignore

    connect_parser = subparsers.add_parser(
        'connect', help='open a web browser that connects to a running dashboard server on \'localhost\''
    )


def dashboard_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    dashboard_command = arguments.dashboard_command

    if dashboard_command == 'connect':
        dashboard.connect()
    else:
        raise exceptions.InvalidStateError('Unknown dashboard command: {}'.format(dashboard_command))


def configure_generator_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-j', '--max-jobs', type=int, default=None, action='store', help='maximum number of jobs generated')
    parser.add_argument('-t', '--job-timeout', type=int, default=None, action='store', help='maximum runtime for a single job in seconds')

    subparsers = parser.add_subparsers(dest='generator_command')
    subparsers.required = True  # type: ignore

    search_subparser = subparsers.add_parser(
        'search',
        help='searches for new pipelines not found in the metalearning database',
    )
    configure_search_parser(search_subparser)

    modify_subparser = subparsers.add_parser(
        'modify',
        help='modifies existing pipelines in the metalearning database',
    )
    configure_modify_parser(modify_subparser)

    update_subparser = subparsers.add_parser(
        'update',
        help='updates existing pipeline runs in the metalearning database to use the current versions of datasets and primitives',
    )
    configure_update_parser(update_subparser)


def generator_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    generator_command = arguments.generator_command
    subparser = parser._subparsers._group_actions[0].choices[generator_command]  # type: ignore

    if generator_command == 'search':
        search_handler(arguments, subparser)
    elif generator_command == 'modify':
        modify_handler(arguments, subparser)
    elif generator_command == 'update':
        update_handler(arguments, subparser)
    else:
        raise exceptions.InvalidStateError('Unknown queue command: {}'.format(generator_command))


def configure_search_parser(parser: argparse.ArgumentParser) -> None:
    pass


def search_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    raise exceptions.NotImplementedError()


def configure_modify_parser(parser: argparse.ArgumentParser) -> None:
    #create the subparsers for the different types of modifications
    
    #seed swapper functionality
    subparsers = parser.add_subparsers(dest='modify_type')
    subparsers.required = True
    swap_seed_subparser = subparsers.add_parser(
         'random-seed',
         description='Uses database data to search pipelines and run functional pipelines on different random seeds',
     )
    #subparser arguments
    swap_seed_subparser.add_argument(
         '--pipeline_id',
         help='The pipeline id to search for in the query, if none, searches all pipelines',
         default=None,
         type=str)
    swap_seed_subparser.add_argument(
         '--submitter',
         help='The pipeline submitter to add to the query',
         default=None,
         type=str)
    swap_seed_subparser.add_argument(
         '--seed_limit',
         help='The amount of random seeds that each ran pipeline will have at the end of the test',
         default=2,
         type=int)
         
    #Primitive swapper functionality
    primitive_swap_subparser = subparsers.add_parser(
        'primitive-swap',
        description='Searches database for pipeline runs containing a primitive and swaps out primitive for a different given primitive')
    #subparser arguments
    primitive_swap_subparser.add_argument(
         '--primitive_id',
         help='The id of the primitive to swap out',
         default=None,
         type=str)
    primitive_swap_subparser.add_argument(
         '--limit_indeces',
         help='Details for primitive swapping',
         default=None)
    primitive_swap_subparser.add_argument(
         '--swap_primitive_id',
         help='The id of the primitve to swap in',
         default=None,
         type=str)


def modify_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    modify_type = arguments.modify_type
    modify_generator = ModifyGenerator(modify_type, arguments.max_jobs, arguments)
    #now run the enqueuer part
    queue.enqueue_jobs(jobs=modify_generator, job_timeout=arguments.job_timeout)


def configure_update_parser(parser: argparse.ArgumentParser) -> None:
    pass


def update_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    raise exceptions.NotImplementedError()


def configure_worker_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('-w', '--workers', type=int, default=1, action='store', help='the number of workers to start')
    parser.add_argument('-j', '--max-jobs', type=int, default=None, action='store', help='the maximum number of jobs a worker can execute')


def worker_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if arguments.workers < 1:
        raise exceptions.InvalidArgumentValueError('the number of workers must be at least 1')

    for _ in range(arguments.workers):
        queue.start_worker(arguments.max_jobs)
