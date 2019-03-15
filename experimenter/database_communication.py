import collections
import json
import os
import pymongo
import subprocess
from bson import json_util
from d3m.metadata.pipeline import Pipeline
try:
    from .config import real_mongo_port, default_mongo_port, lab_hostname, docker_hostname
except Exception as e:
    print("ERROR: Config File not found. Please follow the instructions in the README")

class PipelineDB:
    """
    This class is a helper function for connecting with the databases holding our info

    Note: Running this file on the command line will export the pipeline runs from the database into the default folder
    as defined below.
    """

    def __init__(self, host_name=lab_hostname, mongo_port=real_mongo_port):
        self.host_name = host_name
        self.mongo_port = mongo_port

        try:
            self.mongo_client = pymongo.MongoClient(self.host_name, self.mongo_port)
        except Exception as e:
            print("Cannot connect to the Mongo Client at port {}. Error is {}".format(self.mongo_port, e))

    def export_pipeline_runs_to_folder(self, folder_directory='~/database/',
                                       collection_names=["pipeline_runs", "pipelines", "datasets", "problems",
                                                         "automl_pipelines", "automl_pipeline_runs"]):
        """
        This function will create or find the directory given and export all pipeline runs from the database to
        the folder.  The pipeline runs are saved as JSON files.
        :param folder_directory: the directory for the pipeline runs to be saved in -> there must be two folders in
        that directory, "pipeline_runs" and "pipelines" unless otherwise specified
        :param collection_names: A list of the collections that documents will be gathered from. Note this name is the
        same as the subfolder that must exist for them to put into
        """
        if not os.path.expanduser(folder_directory):
            # directory not found. Create and give the computer access
            os.mkdir(folder_directory)
            subprocess.call(['chmod', '0777', folder_directory])

        folder_directory = os.path.expanduser(folder_directory)
        # connect to the database
        for collection_name in collection_names:
            output_directory = folder_directory + collection_name + "/"
            db = self.mongo_client.metalearning
            collection = db[collection_name]
            pipeline_runs_cursor = collection.find({})
            # go through each pipeline run
            for doc in pipeline_runs_cursor:
                if collection_name in ["pipeline_runs", "automl_pipeline_runs"]:
                    location, problem_name = self._get_location_of_dataset(doc)
                    file_path = os.path.join(output_directory, "{}_{}_{}{}".format(location, problem_name,
                                                                                   doc['id'], '.json'))
                elif collection_name in ["pipelines", "automl_pipelines"]:
                    predictor_model = doc['steps'][-2]['primitive']['python_path'].split('.')[-2]
                    try:
                        type = doc['steps'][-2]['primitive']['python_path'].split('.')[-3]
                    except Exception as e:
                        type = "unknown"
                    file_path = os.path.join(output_directory, "{}_{}_{}_{}{}".format(type, predictor_model, doc['id'],
                                                                                   "pipeline", '.json'))
                elif collection_name == "problems":
                    file_path = os.path.join(output_directory, "{}".format(doc["about"]["problemID"]))

                elif collection_name == "datasets":
                    file_path = os.path.join(output_directory, "{}".format(doc["about"]["datasetID"]))

                else:
                    print("ERROR: Not a valid collection name")
                    raise Exception

                if not os.path.isfile(file_path):
                    with open(file_path, 'w') as f:
                        json.dump(doc, f, indent=2, default=json_util.default)
                    # give permission to open the files
                    subprocess.call(['chmod', '0777', file_path])

            print("There were {} files were exported from {}.".format(pipeline_runs_cursor.count(), collection_name))

    def erase_mongo_database(self, are_you_sure=False):
        """
        Erases all collections of the database, for debug purposes.
        """
        if are_you_sure:
            db = self.mongo_client.metalearning
            print("Clearing pipeline_runs collection")
            db.pipeline_runs.remove({})
            print("Clearing pipeline collection")
            db.pipelines.remove({})
            print("Clearing datasets collection")
            db.datasets.remove({})
            print("Clearing problems collection")
            db.problems.remove({})

    def has_duplicate_pipeline_run(self, problem, pipeline, collection_name):
        """
         Used by experimenter_driver.py to check whether or not to run a pipeline on a specific problem
         :return True if the pipeline has been run, False if it hasn't
         """
        db = self.mongo_client.metalearning
        collection = db[collection_name]
        pipeline_id = pipeline["id"]
        dataset_id = problem.split("/")[-1] + "_dataset"
        if collection.find({"$and": [{"pipeline.id": pipeline_id}, {"datasets.id": dataset_id}]}).count():
            return True
        else:
            return False

    def add_to_pipeline_runs_mongo(self, pipeline_run, collection_name):
        """
        Adds a pipeline run to the database.  Minimal error checking as we assume "has_duplicate_pipeline_run" has been run.
        """
        db = self.mongo_client.metalearning
        collection = db[collection_name]
        if not collection.find({"id": pipeline_run['id']}).count():
            pipeline_run_id = collection.insert_one(pipeline_run).inserted_id
            print("Wrote pipeline run to the database with inserted_id: {}".format(pipeline_run_id))
        else:
            print("\n\nWARNING: PIPELINE_RUN ALREADY EXISTS IN DATABASE. NOTHING WRITTEN.\n\n")

    def add_to_pipelines_mongo(self, new_pipeline):
        """
        Function to add a pipeline to the mongodb database of pipelines.
        :return False if the database already contains it, True if the pipeline was added to the database
        """
        db = self.mongo_client.metalearning
        collection = db.pipelines
        new_pipeline_json = new_pipeline.to_json_structure()
        digest = new_pipeline_json["digest"]
        id = new_pipeline_json["id"]

        # simple checks to validate pipelines and potentially save time
        if collection.find({"digest": digest}).count():
            return False

        if collection.find({"id": id}).count():
            return False

        # deep comparison of equality
        pipelines_cursor = collection.find({})
        for pipeline in pipelines_cursor:
            pipeline_to_compare = Pipeline.from_json(json.dumps(pipeline, sort_keys=True, indent=4,
                                                                default=json_util.default))
            if new_pipeline.equals(pipeline_to_compare):
                return False
        else:
            pipeline_id = collection.insert_one(new_pipeline.to_json_structure()).inserted_id
            print("Wrote pipeline to the database with inserted_id from mongo: {}".format(pipeline_id))
            return True

    def find_mongo_pipeline_run_by_id(self, pipeline_run_id):
        db = self.mongo_client.metalearning
        collection = db.pipeline_runs
        return collection.find({"id": pipeline_run_id}).count()

    def find_mongo_pipeline_by_primitive_ids(self, problem, primitives_string):
        # Attempt to uniquely identify a pipeline_run by the combination of inputs and pipeline
        problem_name = problem.split('/')[-1]
        primitives_id_string = problem_name + primitives_string

        db = self.mongo_client.metalearning
        collection = db.pipeline_runs
        return collection.find({"primitives_used": primitives_id_string}).count()

    def _get_location_of_dataset(self, doc):
        """
        :return min_name: what directory of problems it came from (seed, LL0, LL1)
        :return problem_name: the name of the problem (i.e. 185_baseball)
        """
        enum_of_paths = ["seed", "LL0", "LL1"]
        path = ""
        # TODO: this is super ugly but the only way I can find to do this
        # try to get the URI from the docs. Depending on the pipeline this is the first through the third.
        for index in range(3):
            try:
                path = doc["steps"][0]["method_calls"][index]["metadata"]["produce"][0]["metadata"]['location_uris'][0]
                # get the third to last folder name -> it's the name of the problem.
                problem_name = path.split("/")[-3]
            except Exception:
                print("WARNING: could not get the URI")
                return "unknown", "unknown"

        # search for the first one of these. The first one to appear is which folder it is in.
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

    def get_all_pipelines(self, baselines=False):
        """
        Used to gather pipelines for the experimenter_driver.py
        :param baselines: a bool, indicating whether or not to grab the regular pipelines or the automl pipelines
        :returns a dictionary with two keys "classification" and "regression" each full of pipelines from the database
        """
        pipelines = {"classification": [], "regression": []}
        db = self.mongo_client.metalearning
        collection = db.pipelines if not baselines else db.automl_pipelines
        pipeline_cursor = collection.find({})
        for index, pipeline in enumerate(pipeline_cursor):
            predictor_model = pipeline['steps'][-2]['primitive']['python_path'].split('.')[-3]
            pipelines[predictor_model].append(Pipeline.from_json(json.dumps(pipeline, sort_keys=True, indent=4,
                                                                            default=json_util.default)))
        return pipelines, len(pipelines["regression"]) + len(pipelines["classification"])

    def add_to_problems(self, problem_doc):
        """
        A function for adding to the problems collection
        :param problem_doc: the problem document
        :return: bool indicating whether or not the document was inserted
        """
        db = self.mongo_client.metalearning
        collection = db.problems
        id = problem_doc["about"]["problemID"]

        if collection.find({"about.problemID": id}).count():
            return False

        pipeline_id = collection.insert_one(problem_doc).inserted_id
        print("Wrote PROBLEM to the database with inserted_id from mongo: {}".format(pipeline_id))
        return True

    def add_to_datasets(self, dataset_doc):
        """
        A function for adding to the problems collection
        :param dataset_doc: the dataset document describing the dataset
        :return: bool indicating whether or not the document was inserted
        """
        db = self.mongo_client.metalearning
        collection = db.datasets
        id = dataset_doc["about"]["datasetID"]
        digest = dataset_doc["about"]["digest"]

        if collection.find({"about.digest": digest}).count():
            return False

        if collection.find({"about.datasetID": id}).count():
            return False

        pipeline_id = collection.insert_one(dataset_doc).inserted_id
        print("Wrote PROBLEM to the database with inserted_id from mongo: {}".format(pipeline_id))
        return True

    def add_to_automl_pipelines(self, new_pipeline):
        """
        Function to add a pipeline to the mongodb collection of automl_pipelines.
        :return False if the database already contains it, True if the pipeline was added to the database
        """
        db = self.mongo_client.metalearning
        collection = db.automl_pipelines
        new_pipeline_json = new_pipeline.to_json_structure()
        new_pipeline_steps = primitive_list_from_pipeline_json(new_pipeline_json)
        digest = new_pipeline_json["digest"]
        id = new_pipeline_json["id"]

        # simple checks to validate pipelines and potentially save time
        if collection.find({"digest": digest}).count():
            return False

        if collection.find({"id": id}).count():
            return False

        # deep comparison of equality
        pipelines_cursor = collection.find({})
        for pipeline in pipelines_cursor:
            pipeline_steps_to_compare = primitive_list_from_pipeline_json(pipeline)
            if pipeline_steps_to_compare == new_pipeline_steps:
                return False
        else:
            pipeline_id = collection.insert_one(new_pipeline.to_json_structure()).inserted_id
            print("Wrote automl pipeline to the database with inserted_id from mongo: {}".format(pipeline_id))
            return True

"""
A helper function to return all the primitives used in a pipeline
Duplicate of one in execute_pipeline.py but cannot import it due to RQ limitations

:param pipeline_json a pipeline object in JSON form
"""

def primitive_list_from_pipeline_json(pipeline_json):
    primitives = []
    for step in pipeline_json['steps']:
        primitives.append(step['primitive']['python_path'])
    return primitives

