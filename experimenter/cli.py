import argparse
import typing

from experimenter import queue


def main(argv: typing.Sequence) -> None:
    parser = argparse.ArgumentParser(prog='experimenter')
    configure_parser(parser)
    arguments = parser.parse_args(argv[1:])
    handler(arguments, parser)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest='experimenter_command')
    subparsers.required = True

    queue_parser = subparsers.add_parser('queue')
    configure_queue_parser(queue_parser)


def handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    experimenter_command = arguments.experimenter_command
    subparser = parser._subparsers._group_actions[0].choices[experimenter_command]  # type: ignore

    if experimenter_command == 'queue':
        queue_handler(arguments, subparser)
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
