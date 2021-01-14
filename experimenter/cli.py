import argparse
import typing

from experimenter import job_queue


def main(argv: typing.Sequence) -> None:
    parser = argparse.ArgumentParser(prog='experimenter')
    configure_parser(parser)
    arguments = parser.parse_args(argv[1:])
    handler(arguments, parser)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest='experimenter_command')

    job_queue_parser = subparsers.add_parser('job-queue')
    configure_job_queue_parser(job_queue_parser)


def configure_job_queue_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest='job_queue_command')

    start_parser = subparsers.add_parser('start')
    start_parser.add_argument('--port', type=int, default=6379, action='store')
    start_parser.add_argument('--data-path', type=str, default='/d3m_experimenter_cache')

    stop_parser = subparsers.add_parser('stop')


def handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    experimenter_command = arguments.experimenter_command
    subparser = parser._subparsers._group_actions[0].choices[experimenter_command]  # type: ignore

    if experimenter_command == 'job-queue':
        job_queue_handler(arguments, subparser)
    else:
        raise Exception('Unknown experimenter command: {}'.format(experimenter_command))


def job_queue_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    job_queue_command = arguments.job_queue_command

    if job_queue_command == 'start':
        job_queue.start_job_queue(arguments.port, arguments.data_path)
    elif job_queue_command == 'stop':
        job_queue.stop_job_queue()
    else:
        raise Exception('Unknown job-queue command: {}'.format(job_queue_command))
