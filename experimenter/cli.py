import argparse
import typing

from experimenter import exceptions, queue


def main(argv: typing.Sequence) -> None:
    parser = argparse.ArgumentParser(prog='experimenter')
    configure_parser(parser)
    arguments = parser.parse_args(argv[1:])
    handler(arguments, parser)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest='experimenter_command')
    subparsers.required = True

    queue_parser = subparsers.add_parser(
        'queue',
        description='control the job queue',
    )
    configure_queue_parser(queue_parser)

    generator_parser = subparsers.add_parser(
        'generator',
        description='generates new pipelines and queues them to run on available datasets',
    )
    configure_generator_parser(generator_parser)

    worker_parser = subparsers.add_parser(
        'worker',
        description='creates a worker to run jobs on pushed onto the queue by a generator',
    )
    configure_worker_parser(worker_parser)


def handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    experimenter_command = arguments.experimenter_command
    subparser = parser._subparsers._group_actions[0].choices[experimenter_command]  # type: ignore

    if experimenter_command == 'queue':
        queue_handler(arguments, subparser)
    elif experimenter_command == 'generator':
        generator_handler(arguments, subparser)
    elif experimenter_command == 'worker':
        worker_handler(arguments, subparser)
    else:
        raise exceptions.InvalidStateError('Unknown experimenter command: {}'.format(experimenter_command))


def configure_queue_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest='queue_command')
    subparsers.required = True

    start_parser = subparsers.add_parser('start')
    start_parser.add_argument('--port', type=int, default=queue.DEFAULT_HOST_PORT, action='store')
    start_parser.add_argument('--data-path', type=str, default=queue.DEFAULT_HOST_DATA_PATH)

    stop_parser = subparsers.add_parser('stop')

    status_parser = subparsers.add_parser('status')


def queue_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    queue_command = arguments.queue_command

    if queue_command == 'start':
        queue.start(arguments.port, arguments.data_path)
    elif queue_command == 'stop':
        queue.stop()
    elif queue_command == 'status':
        queue.status()
    else:
        raise exceptions.InvalidStateError('Unknown queue command: {}'.format(queue_command))


def configure_generator_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--n-max-jobs', type=int, default=None, action='store')  # TODO:, description='the max number of jobs to generate')

    subparsers = parser.add_subparsers(dest='generator_command')
    subparsers.required = True

    search_subparser = subparsers.add_parser(
        'search',
        description='searches for new pipelines not found in the metalearning database',
    )
    configure_search_parser(search_subparser)

    edit_subparser = subparsers.add_parser(
        'modify',
        description='modifies existing pipelines in the metalearning database',
    )
    configure_edit_parser(edit_subparser)

    update_subparser = subparsers.add_parser(
        'update',
        description='updates existing pipeline runs in the metalearning database to use the current versions of datasets and primitives',
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


def configure_edit_parser(parser: argparse.ArgumentParser) -> None:
    pass


def modify_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    raise exceptions.NotImplementedError()


def configure_update_parser(parser: argparse.ArgumentParser) -> None:
    pass


def update_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    raise exceptions.NotImplementedError()


def configure_worker_parser(parser: argparse.ArgumentParser) -> None:
    pass


def worker_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    raise exceptions.NotImplementedError()
