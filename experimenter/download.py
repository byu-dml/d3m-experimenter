import logging
import typing

from elasticsearch import Elasticsearch

from experimenter import d3m_db, utils


logger = logging.getLogger(__name__)


def generate_download_jobs(d3m_index: str, job_size: int, batch_size: int) -> typing.Generator[typing.Dict, None, None]:
    min_timestamp, max_timestamp = d3m_db.get_index_timestamp_range(d3m_index)
    # ensures the latest document in the index gets downloaded
    max_timestamp = utils.timestamp_add_epsilon(max_timestamp, seconds=1)

    # stack prioritizes most recent documents first
    timestamp_stack = [(min_timestamp, max_timestamp)]
    while timestamp_stack:
        start, end = timestamp_stack.pop()

        local_count = 0  # TODO
        d3m_count = d3m_db.count(d3m_index, start, end)

        if local_count < d3m_count:
            if d3m_count > job_size:
                midpoint = utils.timestamp_range_midpoint(start, end)
                timestamp_stack.append((start, midpoint))
                timestamp_stack.append((midpoint, end))

            else:
                yield utils.format_job(download, d3m_index, start, end, batch_size, d3m_index)

        # elif local_count > d3m_count:
        #     logger.critical('')


def download(d3m_index, start, end, batch_size, local_collection):
    pass
