
import logging
logger = logging.getLogger(__name__)
from experimenter.database_communication import PipelineDB
import argparse

"""
COMMAND LINE ARGUMENTS:

Arguments:
type: either "get" to get files from the database, or "erase" to erase all files from the database
folder: the directory to store the json files, if not the default

Example Usage:
"python3 get_documents.py" (gets all the pipeline runs and pipelines and stores them in json files in the
default folders)

"python3 get_documents.py name_of_folder" (gets all the pipeline runs and pipelines and stores them in
name_of_folder)

"python3 get_documents.py erase" (erases all pipelines and pipeline runs from the database)

"""
def main(type_of_run, folder_directory):
    # the following block gets the command line argument and if none is given, marks it as "get files"
    db = PipelineDB()
    if type_of_run == "get":
        if folder_directory is not None:
            db.export_pipeline_runs_to_folder(folder_directory)
        else:
            db.export_pipeline_runs_to_folder()

    # used for debugging
    elif type_of_run == "erase":
        db.erase_mongo_database(True)

    elif type_of_run == "check":
        db.get_database_stats()

    elif type_of_run == "visualize-time":
        values = db.get_pipeline_run_time_distribution()
        import pdb; pdb.set_trace()
        import pandas as pd
        import numpy as np
        df_time = pd.DataFrame(values)
        df_time.to_csv("all_pipeline_runs")
        df_time.groupby("dataset").mean().to_csv("aggregate_all_pipeline_runs.csv")
        logger.info("The datasets with means over 20:")
        logger.info(np.mean(df_time["time"] > 20*60))

    elif type_of_run == "visualize-score":
        values = db.get_pipeline_run_score_distribution()
        import pandas as pd
        import numpy as np
        df_time = pd.DataFrame(values)
        df_time.to_csv("all_pipeline_runs_score.csv")
        df_time.groupby("dataset").mean().to_csv("average_score_all_pipeline_runs.csv")


# in case you want to just run the file
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-type", '-t', help="Whether to 'get' all runs or to 'erase' all runs from the database",
                        choices=["get", "erase", "check", "visualize-time", "visualize-score"], default="get")
    parser.add_argument("-folder", '-f', help="The path of the folder you want the json files stored in")
    args = parser.parse_args()
    main(args.type, args.folder)
