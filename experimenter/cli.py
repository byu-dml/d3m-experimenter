import argparse
import typing

from experimenter import d3m_db, download as download_module, exceptions, queue


def main(argv: typing.Sequence) -> None:
    parser = argparse.ArgumentParser(prog='experimenter')
    configure_parser(parser)
    arguments = parser.parse_args(argv[1:])
    handler(arguments, parser)


def configure_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest='experimenter_command')
    subparsers.required = True  # type: ignore

    queue_parser = subparsers.add_parser(
        'queue', help='control the job queue',
    )
    configure_queue_parser(queue_parser)

    download_parser = subparsers.add_parser(
        'download', help='download documents from the D3M metalearning database',
    )
    configure_download_parser(download_parser)


def handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    experimenter_command = arguments.experimenter_command
    subparser = parser._subparsers._group_actions[0].choices[experimenter_command]  # type: ignore

    if experimenter_command == 'queue':
        queue_handler(arguments, subparser)
    elif experimenter_command == 'download':
        download_handler(arguments, subparser)
    else:
        raise exceptions.InvalidStateError('Unknown experimenter command: {}'.format(experimenter_command))


def configure_queue_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest='queue_command')
    subparsers.required = True  # type: ignore

    status_parser = subparsers.add_parser('status', help='get queue status (started or stopped)')

    empty_parser = subparsers.add_parser('empty', help='remove all jobs from a queue')
    empty_parser.add_argument('-q', '--queue-name', help='the name of the queue to empty')


def queue_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    queue_command = arguments.queue_command

    if queue_command == 'status':
        queue.status()
    elif queue_command == 'empty':
        queue.empty(arguments.queue_name)
    else:
        raise exceptions.InvalidStateError('Unknown queue command: {}'.format(queue_command))


def configure_download_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--indexes', nargs='+', choices=d3m_db.D3M_INDEXES, default=d3m_db.D3M_INDEXES,
        help='which indexes to download, respects the order provided',
    )
    parser.add_argument(
        '--job-size', type=int, default=100, help='the max number of documents to download in a single database query'
    )
    parser.add_argument(
        '--batch-size', type=int, default=10, help='the database query batch size'
    )


def download_handler(arguments: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    for index in arguments.indexes:
        job_generator = download_module.generate_download_jobs(index, arguments.job_size, arguments.batch_size)
        # TODO: put on a different queue?
        queue.enqueue_jobs(job_generator)
