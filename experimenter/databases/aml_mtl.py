import logging
import json
import os
import pymongo
import subprocess
import re
from typing import List
from bson import json_util, ObjectId
from d3m.metadata.pipeline import Pipeline
from dateutil.parser import parse
from experimenter.pipeline_builder import EZPipeline
from experimenter.config import MONGO_HOST, MONGO_PORT

logger = logging.getLogger(__name__)


class PipelineDB:
    """
    This class is a helper function for connecting with the databases holding our info.
    It interfaces with the BYU Applied Machine Learning lab's MongoDB metalearning
    database.

    Note: Running this file on the command line will export the pipeline runs from the
    database into the default folder as defined below.
    """

    def __init__(self, mongo_host: str = MONGO_HOST, mongo_port: int = MONGO_PORT):
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port

        try:
            self.mongo_client = pymongo.MongoClient(self.mongo_host, self.mongo_port)
            self.db = self.mongo_client.metalearning
        except Exception as e:
            logger.info(
                "Cannot connect to the Mongo Client at port {}. Error is {}".format(
                    self.mongo_port, e
                )
            )

    def export_pipeline_runs_to_folder(
        self,
        folder_directory: str = "~/database/",
        collection_names: list = ["pipeline_runs", "pipelines", "datasets", "problems"],
    ):
        """
        This function will create or find the directory given and export all pipeline
        runs from the database to the folder. The pipeline runs are saved as JSON files.

        :param folder_directory: the directory for the pipeline runs to be saved in ->
            there must be two folders in that directory, "pipeline_runs" and "pipelines"
            unless otherwise specified
        :param collection_names: A list of the collections that documents will be
            gathered from. Note this name is the same as the subfolder that must exist
            for them to put into
        """
        if not os.path.expanduser(folder_directory):
            # directory not found. Create and give the computer access
            os.mkdir(folder_directory)
            subprocess.call(["chmod", "0777", folder_directory])

        folder_directory = os.path.expanduser(folder_directory)
        # connect to the database
        for collection_name in set(collection_names):
            output_directory = folder_directory + collection_name + "/"
            collection = self.db[collection_name]
            pipeline_runs_cursor = collection.find({})
            # go through each pipeline run
            for doc in pipeline_runs_cursor:
                if collection_name == "pipeline_runs":
                    location, problem_name = self._get_location_of_dataset(doc)
                    file_path = os.path.join(
                        output_directory,
                        "{}_{}_{}{}".format(location, problem_name, doc["id"], ".json"),
                    )
                elif collection_name == "pipelines":
                    predictor_model = doc["steps"][-2]["primitive"][
                        "python_path"
                    ].split(".")[-2]
                    try:
                        type = doc["steps"][-2]["primitive"]["python_path"].split(".")[
                            -3
                        ]
                    except Exception:
                        type = "unknown"
                    file_path = os.path.join(
                        output_directory,
                        "{}_{}_{}_{}{}".format(
                            type, predictor_model, doc["id"], "pipeline", ".json"
                        ),
                    )
                elif collection_name == "problems":
                    file_path = os.path.join(
                        output_directory, "{}".format(doc["about"]["problemID"])
                    )

                elif collection_name == "datasets":
                    file_path = os.path.join(
                        output_directory, "{}".format(doc["about"]["datasetID"])
                    )

                else:
                    logger.info("ERROR: Not a valid collection name")
                    raise Exception

                if not os.path.isfile(file_path):
                    with open(file_path, "w") as f:
                        json.dump(doc, f, indent=2, default=json_util.default)
                    # give permission to open the files
                    subprocess.call(["chmod", "0777", file_path])

            logger.info(
                "There were {} files were exported from {}.".format(
                    collection.count_documents({}), collection_name
                )
            )

    def get_database_stats(self):
        """
        This function will tell us how many items are in each collection
        """
        for collection_name in self.db.list_collection_names():
            collection = self.db[collection_name]
            sum_docs = collection.estimated_document_count()
            logger.info(
                "There are ~{} documents in {}".format(sum_docs, collection_name)
            )

    def erase_mongo_database(self, are_you_sure: bool = False):
        """
        Erases all collections of the database, for debug purposes.

        :param are_you_sure: a check to make sure you're ready for the consequences
        """
        pass
        # if are_you_sure:
        #     for collection_name in self.db.list_collection_names():
        #         logger.info(f"Clearing {collection_name} collection")
        #         self.db[collection_name].remove({})

    def add_to_pipelines_mongo(self, new_pipeline: EZPipeline) -> bool:
        """
        Function to add a pipeline to the mongodb database of pipelines.

        :param new_pipeline: the new pipeline to add to mongo
        :return False if the database already contains it, True if the pipeline was
            added to the database
        """
        collection = self.db.pipelines_to_run
        new_pipeline_json = new_pipeline.to_json_structure()
        digest = new_pipeline_json["digest"]
        id = new_pipeline_json["id"]

        # validate pipeline
        new_pipeline.check()

        # simple checks to validate pipelines and potentially save time
        if collection.count_documents({"digest": digest}):
            return False

        if collection.count_documents({"id": id}):
            return False
        #
        # # deep comparison of equality
        # pipelines_cursor = collection.find({})
        # for index, pipeline in enumerate(pipelines_cursor):
        #     try:
        #         # forgo this for now until we can get it to work.
        #         # pipeline_to_compare = Pipeline.from_json(json.dumps(pipeline, sort_keys=True, indent=4,
        #         #                                                     default=json_util.default))
        #         # if new_pipeline.equals(pipeline_to_compare):
        #         #     return False
        #         if primitive_list_from_pipeline_json(pipeline) == primitive_list_from_pipeline_json(new_pipeline_json):
        #             return False
        #
        #     except Exception as e:
        #         logger.info(e)
        #         raise(e)
        #
        # else:
        pipeline_id = collection.insert_one(new_pipeline_json).inserted_id
        logger.info(
            "Wrote pipeline to the database with inserted_id from mongo: {}".format(
                pipeline_id
            )
        )
        return True

    def remove_all_pipelines_mongo(self) -> None:
        self.db.pipelines_to_run.remove({})

    def _get_location_of_dataset(self, doc: dict) -> tuple((str, str)):
        """
        Checks a dataset document to find whether it is "seed", "LL0", or "LL1".

        :param doc: the document to query
        :return min_name: what directory of problems it came from (seed, LL0, LL1)
        :return problem_name: the name of the problem (i.e. 185_baseball_MIN_METADATA)
        """
        enum_of_paths = ["seed", "LL0", "LL1"]
        path = ""
        # TODO: this is super ugly but the only way I can find to do this
        # try to get the URI from the docs. Depending on the pipeline this is the first
        # through the third.
        for index in range(3):
            try:
                path = doc["steps"][0]["method_calls"][index]["metadata"]["produce"][0][
                    "metadata"
                ]["location_uris"][0]
                # get the third to last folder name -> it's the name of the problem.
                problem_name = path.split("/")[-3]
            except Exception:
                logger.info("WARNING: could not get the URI")
                return "unknown", "unknown"

        # search for the first one of these. The first one to appear is which folder
        # it is in.
        seed = path.find(enum_of_paths[0])
        LL0 = path.find(enum_of_paths[1])
        LL1 = path.find(enum_of_paths[2])
        min_value = float("inf")
        min_name = "ERROR"
        # find the minimum
        for index, check in enumerate([seed, LL0, LL1]):
            if check > 0 and check < min_value:
                min_name = enum_of_paths[index]
                min_value = check

        return min_name, problem_name

    def is_phrase_in(self, phrase: str, text: str) -> bool:
        """
        A helper function for regex-ing through text.

        :param phrase: the phrase to look in the text for
        :param text: the text to be searched
        :return a boolean of whether the phrase exists
        """
        return re.search(r"\b{}\b".format(phrase), text, re.IGNORECASE) is not None

    def get_all_pipelines(self) -> dict:
        """
        Used to gather pipelines for the `experimenter_driver.py`.

        :return: a dictionary with two keys "classification" and "regression" each full
            of pipelines from the database
        """
        pipelines = {"classification": [], "regression": []}
        collection = self.db.pipelines_to_run
        pipeline_cursor = collection.find({})
        for index, pipeline in enumerate(pipeline_cursor):
            if index % 1000 == 0:
                logger.info("On pipeline number {}".format(index))
            is_classification = self.is_phrase_in(
                "d3m.primitives.classification", json.dumps(pipeline["steps"])
            )
            is_regression = self.is_phrase_in(
                "d3m.primitives.regression", json.dumps(pipeline["steps"])
            )
            if is_classification and is_regression:
                raise Exception(
                    f"cannot use pipeline (digest={pipeline['digest']}) for "
                    "both regression and classification"
                )
            elif is_classification:
                predictor_model = "classification"
            elif is_regression:
                predictor_model = "regression"
            else:
                raise Exception(
                    "could not find classification or regression "
                    f"for pipeline (digest={pipeline['digest']})"
                )
            pipeline_json = json.dumps(
                pipeline, sort_keys=True, indent=4, default=json_util.default
            )
            pipelines[predictor_model].append(Pipeline.from_json(pipeline_json))
        return (
            pipelines,
            len(pipelines["regression"]) + len(pipelines["classification"]),
        )

    def remove_pipelines_containing(self, bad_primitives: List[str]):
        """
        A function to deleting all pipelines that contain bad primitives
        :param bad_primitives: a list of primitive ids
        """
        delete_these_pipelines = []
        collection = self.db.pipelines_to_run
        pipeline_cursor = collection.find({})
        for pipeline in pipeline_cursor:
            pipeline_steps_to_compare = primitive_list_from_pipeline_json(pipeline)
            for primitive in bad_primitives:
                if primitive in pipeline_steps_to_compare:
                    delete_these_pipelines.append(pipeline["_id"])
                    break

        # so you can check before you delete everything
        import pdb

        pdb.set_trace()

        for document_id in delete_these_pipelines:
            collection.delete_one({"_id": ObjectId(document_id)})

    def get_pipeline_run_time_distribution(self):
        """
        This function will tell us the times of each pipeline_run approx.
        """
        collection_names = ["pipeline_runs"]
        # connect to the database
        list_of_times = []
        logger.info("Collecting Times...")
        for collection_name in collection_names:
            collection = self.db[collection_name]
            pipeline_runs_cursor = collection.find({})
            # go through each pipeline run
            for index, doc in enumerate(pipeline_runs_cursor):
                if index % 10000 == 0:
                    logger.info("At {} documents parsed".format(index))
                dataset = doc["datasets"][0]["id"]
                begin = doc["steps"][0]["method_calls"][0]["start"]
                begin_val = parse(begin)
                end = doc["steps"][-1]["method_calls"][-1]["end"]
                end_val = parse(end)
                total_time = (end_val - begin_val).total_seconds()
                list_of_times.append({"time": total_time, "dataset": dataset})

        return list_of_times

    def add_to_metafeatures(self, pipeline_run: dict):
        """
        Adds a pipeline_run to the metafeatures collection
        :param pipeline_run: the pipeline_run to add
        """
        collection = self.db.metafeatures
        pipeline_id = pipeline_run["pipeline"]["id"]
        dataset_id = pipeline_run["datasets"][0]["id"]

        if not collection.count_documents(
            {"$and": [{"pipeline.id": pipeline_id}, {"datasets.id": dataset_id}]}
        ):
            pipeline_run_id = collection.insert_one(pipeline_run).inserted_id
            logger.info(
                "Wrote metafeature pipeline run to "
                f"the database with inserted_id: {pipeline_run_id}"
            )
        else:
            logger.info(
                "\n\nWARNING: PIPELINE_RUN ALREADY "
                "EXISTS IN DATABASE. NOTHING WRITTEN.\n\n"
            )

    def get_pipeline_run_score_distribution(self):
        """
        This function will give us the scores from every pipeline run
        """
        collection_names = ["pipeline_runs"]
        # connect to the database
        list_of_times = []
        logger.info("Collecting Times...")
        for collection_name in collection_names:
            collection = self.db[collection_name]
            pipeline_runs_cursor = collection.find({})
            # go through each pipeline run
            for index, doc in enumerate(pipeline_runs_cursor):
                if index % 10000 == 0:
                    logger.info("At {} documents parsed".format(index))
                metric = doc["run"]["results"]["scores"][0]["metric"]["metric"]
                if metric == "F1_MACRO":
                    dataset = doc["datasets"][0]["id"]
                    score = doc["run"]["results"]["scores"][0]["value"]
                    list_of_times.append({"score": score, "dataset": dataset})

        return list_of_times

    def metafeature_run_already_exists(self, problem: str, pipeline: dict) -> int:
        """
        A function to check if a metafeature run already exists
        :param problem: the problem to check the pipeline with
        :param pipeline: the metafeature pipeline
        :return a count of existing pipelines
        """
        collection = self.db.metafeatures
        pipeline_id = pipeline["id"]
        dataset_id = problem
        logger.info(problem)
        exit(0)
        check = collection.count_documents(
            {"$and": [{"pipeline.id": pipeline_id}, {"datasets.id": dataset_id}]}
        )
        return check


def primitive_list_from_pipeline_json(pipeline_json: dict):
    """
    A helper function to return all the primitives used in a pipeline
    Duplicate of one in execute_pipeline.py but cannot import it due to RQ limitations

    :param pipeline_json a pipeline object in JSON form
    """
    primitives = []
    for step in pipeline_json["steps"]:
        primitives.append(step["primitive"]["python_path"])
    return primitives
