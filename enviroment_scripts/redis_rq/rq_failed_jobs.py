#!/usr/bin/env python

import os
from rq import Connection, Worker, get_failed_queue
import redis
import re


def is_phrase_in(phrase, text):
    return re.search(r"\b{}\b".format(phrase), text, re.IGNORECASE) is not None


try:
    redis_host = os.environ["REDIS_HOST"]
    redis_port = int(os.environ["REDIS_PORT"])
except Exception as E:
    print("Exception: environment variables not set")
    raise E

conn = redis.StrictRedis(host=redis_host, port=redis_port)

# Provide queue names to listen to as arguments to this script,
# similar to rq worker
with Connection(connection=conn):
    fq = get_failed_queue()
    map_of_failed_probs = {}
    map_of_failed_for_nan = {}
    map_of_failed_for_timeout = {}
    map_of_failed_for_str = {}
    map_of_failed_memory = {}
    map_of_bad_combinations = {}
    map_of_bad_matrices = {}
    map_bad_rename = {}
    map_workhorse = {}

    total_nan = 0
    total_timeout = 0
    total_failed = 0
    total_str_failure = 0
    total_memory = 0
    total_bad_primitive_comb = 0
    total_bad_matrix = 0
    total_bad_rename = 0
    total_workhorse = 0
    print("Going through failed queue")
    for index, job in enumerate(fq.jobs):
        if index == 500000:
            break
        if not index % 1000:
            print("At {} failed jobs".format(index))
            print(
                "Out of {} failures. {} were from NANs, {} were timeouts, {} memory too large errors, {} bad combinations, "
                "{} bad rename errors, {} bad matrices, and {} were from trying to use str as an int, {} workhorse errors".format(
                    total_failed,
                    total_nan,
                    total_timeout,
                    total_memory,
                    total_bad_primitive_comb,
                    total_bad_rename,
                    total_bad_matrix,
                    total_str_failure,
                    total_workhorse,
                )
            )

        total_failed += 1
        dataset_name = job.args[1].split("/")[-1]
        map_of_failed_probs[dataset_name] = map_of_failed_probs.get(dataset_name, 0) + 1
        error = job.__dict__["exc_info"]
        try:
            is_nan_issue = is_phrase_in(
                "array must not contain infs or NaNs", error
            ) or is_phrase_in(
                "Input contains NaN, infinity or a value too large", error
            )

            is_timeout_issue = is_phrase_in(
                "Task exceeded maximum timeout value", error
            )
            is_memory_error = is_phrase_in("MemoryError", error)

            is_string_bad_type = is_phrase_in(
                "unsupported operand type", error
            ) or is_phrase_in("could not convert string to float", error)

            is_bad_combo = is_phrase_in(
                "Found array with 0 feature", error
            ) or is_phrase_in("For multi-task outputs, use", error)

            is_bad_matrix = is_phrase_in(
                "numpy.linalg.linalg.LinAlgError", error
            ) or is_phrase_in("Internal work array size computation failed", error)

            is_bad_rename = is_phrase_in("rename_duplicate_columns.py", error)

            is_workhorse_error = is_phrase_in(
                "Work-horse process was terminated unexpectedly", error
            )

            if is_nan_issue:
                map_of_failed_for_nan[dataset_name] = (
                    map_of_failed_for_nan.get(dataset_name, 0) + 1
                )
                total_nan += 1
            elif is_timeout_issue:
                map_of_failed_for_timeout[dataset_name] = (
                    map_of_failed_for_timeout.get(dataset_name, 0) + 1
                )
                total_timeout += 1
            elif is_string_bad_type:
                map_of_failed_for_str[dataset_name] = (
                    map_of_failed_for_str.get(dataset_name, 0) + 1
                )
                total_str_failure += 1
            elif is_memory_error:
                map_of_failed_memory[dataset_name] = (
                    map_of_failed_memory.get(dataset_name, 0) + 1
                )
                total_memory += 1
            elif is_bad_combo:
                map_of_bad_combinations[dataset_name] = (
                    map_of_bad_combinations.get(dataset_name, 0) + 1
                )
                total_bad_primitive_comb += 1
            elif is_bad_matrix:
                map_of_bad_matrices[dataset_name] = (
                    map_of_bad_matrices.get(dataset_name, 0) + 1
                )
                total_bad_primitive_comb += 1
            elif is_bad_rename:
                map_bad_rename[dataset_name] = map_bad_rename.get(dataset_name, 0) + 1
                total_bad_rename += 1
            elif is_workhorse_error:
                map_workhorse[dataset_name] = map_workhorse.get(dataset_name, 0) + 1
                is_workhorse_error += 1
            else:
                print(error)

        except Exception as e:
            print(e)
            print("The error it was trying to parse is {}".format(error))
            continue

    print("\n##### TOTAL FAILED #####")
    for key, value in map_of_failed_probs.items():
        print(key, value)

    print("\n##### NAN FAILED #####")
    for key, value in map_of_failed_for_nan.items():
        print(key, value)

    print("\n##### IS MEMORY FAILED #####")
    for key, value in map_of_failed_memory.items():
        print(key, value)

    print("\n##### USING STRING BAD FAILED #####")
    for key, value in map_of_failed_for_str.items():
        print(key, value)

    print("\n##### BAD MATRIX FAILED #####")
    for key, value in map_of_bad_matrices.items():
        print(key, value)

    print("\n##### IS BAD COMBO FAILED #####")
    for key, value in map_of_bad_combinations.items():
        print(key, value)

    print("\n##### IS BAD RENAME FAILED #####")
    for key, value in map_bad_rename.items():
        print(key, value)

    print("\n##### TIMEOUT FAILED #####")
    for key, value in map_of_failed_for_timeout.items():
        print(key, value)

    print("\n\n\n")
    print(
        "Out of {} failures. {} were from NANs, {} were timeouts, {} memory too large errors, {} bad combinations, "
        "{} bad rename errors, {} bad matrices, and {} were from trying to use str as an int, {} workhorse errors".format(
            total_failed,
            total_nan,
            total_timeout,
            total_memory,
            total_bad_primitive_comb,
            total_bad_rename,
            total_bad_matrix,
            total_str_failure,
            total_workhorse,
        )
    )
    print(
        "{} failures are unaccounted for".format(
            total_failed
            - (
                total_nan
                + total_timeout
                + total_str_failure
                + total_memory
                + total_bad_primitive_comb
                + total_bad_matrix
                + total_bad_rename
                + total_workhorse
            )
        )
    )
