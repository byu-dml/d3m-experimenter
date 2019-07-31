from experimenter.experimenter import Experimenter, register_primitives
import os, json, pdb, traceback, sys
from d3m.metadata.pipeline import Pipeline
from experimenter.database_communication import PipelineDB
import warnings, argparse, logging
import redis
from rq import Queue
from execute_pipeline import execute_pipeline_on_problem, execute_fit_pipeline_on_problem

logger = logging.getLogger(__name__)

try:
    redis_host = os.environ['REDIS_HOST']
    redis_port = int(os.environ['REDIS_PORT'])
except Exception as E:
    logger.info("Exception: environment variables not set")
    raise E

class ExperimenterDriver:

    def __init__(self, datasets_dir: str, volumes_dir: str, run_type: str ="all",
                 stored_pipeline_loc=None, distributed=False, generate_automl_pipelines=False, fit_only=False):
        self.datasets_dir = datasets_dir
        self.volumes_dir = volumes_dir
        self.run_type = run_type
        self.distributed = distributed
        self.run_automl = generate_automl_pipelines
        self.fit_only = fit_only

        if run_type == "pipeline_path":
            if stored_pipeline_loc is None:
                self.pipeline_location = "created_pipelines/"
            else:
                self.pipeline_location = stored_pipeline_loc
        else:
            self.pipeline_location = None

        # connect to database
        self.mongo_db = PipelineDB()

        if distributed:
            logger.info("Connecting to Redis")
            try:
                conn = redis.StrictRedis(
                    host=redis_host,
                    port=redis_port)
                if self.fit_only:
                    self.queue = Queue("metafeatures", connection=conn)
                else:
                    self.queue = Queue(connection=conn)
            except:
                raise ConnectionRefusedError


    def primitive_list_from_pipeline_object(self, pipeline):
        primitives = []
        for p in pipeline.steps:
            primitives.append(p.to_json_structure()['primitive']['python_path'])
        return primitives

    def get_list_vertically(self, list):
        return '\n'.join(list)

    def pretty_print_json(self, json_string):
        logger.info("\n\n These are the problems that weren't regression or classification:")
        logger.info(json.dumps(json_string, indent=4))

    def print_pipeline_and_problem(self, pipeline, problem):
        logger.info("Pipeline:")
        logger.info(self.get_list_vertically(self.primitive_list_from_pipeline_object(pipeline)))
        logger.info("on problem {} \n\n".format(problem))

    def handle_keyboard_interrupt(self):
        logger.info('Interrupted')
        traceback.print_exc()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

    def handle_failed_pipeline_run(self, pipeline, problem, error):
        logger.info("\nFailed to run pipeline:\n" + self.get_list_vertically(
            self.primitive_list_from_pipeline_object(pipeline)) + "\n")
        logger.info("On the problem:\n{}\n".format(problem))
        logger.info("ERROR: " + str(error))
        traceback.print_exc()
        logger.info("\n\n")

    def get_pipelines_from_path(self, pipeline_location):
        pipeline_list = {"classification": [], "regression": []}
        for pipeline_name in os.listdir(pipeline_location):
            if pipeline_name.find("regression") != -1:
                type = "regression"
            elif pipeline_name.find("classification") != -1:
                type = "classification"
            # Loading pipeline description file.
            file_path = pipeline_location + pipeline_name
            with open(file_path, 'r') as file:
                pipeline_list[type].append(Pipeline.from_yaml(string_or_file=file))
        return pipeline_list


    def run(self):
        if self.run_type == "pipeline_path":
            logger.info("Executing pipelines found in {}".format(self.pipeline_location))
            if self.pipeline_location is None:
                raise NotADirectoryError
            else:
                pipes = self.get_pipelines_from_path(self.pipeline_location)
                experimenter = Experimenter(self.datasets_dir, self.volumes_dir,
                                            generate_pipelines=False, generate_problems=True)
                problems = experimenter.problems
        # run type is pipelines from mongodb or "all"
        else:
            # generating the pipelines has already been taken care of
            experimenter = Experimenter(self.datasets_dir, self.volumes_dir,
                                        generate_problems=True, generate_pipelines=False)
            problems: dict = experimenter.problems
            if self.fit_only:
                logger.info("Using only the fit pipeline")
                pipes, num_pipes = experimenter.generate_metafeatures_pipeline()
            else:
                logger.info("\n Gathering pipelines from database...")
                pipes, num_pipes = self.mongo_db.get_all_pipelines(baselines=self.run_automl)
            logger.info("There are {} pipelines to be executed".format(num_pipes))

        logger.info("\nExecuting pipelines now")
        # Run classification and regression
        for type_name, pipeline_list in pipes.items():
            if type_name in ["classification", "regression"]:
                logger.info("\n Starting to execute ####{}#### problems".format(type_name))
                for index, problem in enumerate(problems[type_name]):
                    sys.stdout.write('\r')
                    percent = 100 / len(problems[type_name])
                    sys.stdout.write("[%-20s] %d%%" % ('=' * index, percent * index))
                    sys.stdout.flush()
                    for pipe in pipeline_list:
                        if self.mongo_db.should_not_run_pipeline(problem, pipe.to_json_structure(),
                                                                 collection_name= "automl_pipeline_runs" if
                                                                 self.run_automl else "pipeline_runs",
                                                                 skip_pipeline=self.fit_only):
                            logger.info("\n SKIPPING. Pipeline already run.")
                            self.print_pipeline_and_problem(pipe, problem)
                            continue

                        try:
                            # if we are trying to distribute, add to the RQ
                            if self.distributed:
                                if not self.fit_only:
                                    async_results = self.queue.enqueue(execute_pipeline_on_problem, pipe, problem,
                                                                       self.datasets_dir, self.volumes_dir, timeout=60*12)
                                else:
                                    async_results = self.queue.enqueue(execute_fit_pipeline_on_problem, pipe, problem,
                                                                       self.datasets_dir, self.volumes_dir,
                                                                       timeout=60 * 60)
                            else:
                                execute_pipeline_on_problem(pipe, problem, self.datasets_dir, self.volumes_dir)

                        except Exception as e:
                            logger.info("Pipeline execution failed. See {}".format(e))
                            # pipeline didn't work.  Try the next one
                            raise e

        self.pretty_print_json(experimenter.incorrect_problem_types)  # For debugging purposes



"""
Options for command line interface
--run-type: "all", "execute", "generate", "distribute", or "pipelines_path" (controls whether to generate and run 
            pipelines or just to run pipelines from a folder)
--pipeline-folder: string of the file_path to the folder containing the pipelines. Used in combination with --run-type
--run-baselines: a flag used for choosing to run only AutoML systems. By default this is off.  The previous flags work 
            independently of this one.

Examples:
python3 experimenter_driver.py (runs and generates all pipelines from mongodb on all problems)
python3 experimenter_driver.py -r all (runs all pipelines from mongodb on all problems)

python3 experimenter_driver.py -r execute (runs all pipelines from mongodb on all problems)
python3 experimenter.py -r execute -f default (takes pipelines from default folder "experimenter/created_pipelines/")
python3 experimenter.py -r execute -f other_folder/ (takes pipelines from "other_folder/")

python3 experimenter_driver.py -r distribute (takes pipelines from the database and adds jobs to the RQ queue)

python3 experimenter.py -r pipeline_path -f default (takes pipelines from default folder "experimenter/created_pipelines/")
python3 experimenter.py -r pipeline_path -f other_folder/ (takes pipelines from default folder "other_folder/")

python3 experimenter.py -r generate (creates pipelines and stores them in mongodb)
python3 experimenter.py -r generate -f default (creates pipelines in default folder "experimenter/created_pipelines/")
python3 experimenter.py -r generate -f other_folder/ (creates pipelines and stores them in "other_folder/")

python3 experimenter_driver.py -r all -b (creates AutoML pipelines on all problems and executes them)
python3 experimenter.py -r generate -b (creates AutoML system pipelines and stores them in mongodb)
python3 experimenter_driver.py -r distribute -b (takes AutoML pipelines from the database and adds jobs to the RQ queue)
python3 experimenter.py -r execute -b (takes AutoML pipelines from the database and executes them)
"""
def main(run_type, pipeline_folder, run_baselines, only_run_fit):

    datasets_dir = '/datasets'
    volumes_dir = '/volumes'

    if run_baselines:
        register_primitives()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.CRITICAL)

    # annoyed with D3M namespace warnings
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': True,
    })
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        if run_type == "all":
            # Generate all possible problems and get pipelines - use default directory, classifiers, and preprocessors
            experimenter = Experimenter(datasets_dir, volumes_dir, generate_pipelines=True,
                                        generate_problems=True, generate_automl_pipelines=run_baselines)

        elif run_type == "generate":
            logger.info("Only generating pipelines...")
            experimenter = Experimenter(datasets_dir, volumes_dir, generate_pipelines=True,
                                        location=pipeline_folder, generate_automl_pipelines=run_baselines)
            return

        elif run_type == "distribute":
            if not only_run_fit:
                experimenter_driver = ExperimenterDriver(datasets_dir, volumes_dir,
                                                         run_type=run_type, stored_pipeline_loc=pipeline_folder,
                                                         distributed=True, generate_automl_pipelines=run_baselines)
                experimenter_driver.run()

                return
            else:
                experimenter_driver = ExperimenterDriver(datasets_dir, volumes_dir,
                                                         run_type=run_type, stored_pipeline_loc=pipeline_folder,
                                                         distributed=True, generate_automl_pipelines=run_baselines,
                                                         fit_only=only_run_fit)
                experimenter_driver.run()

                return

        experimenter_driver = ExperimenterDriver(datasets_dir, volumes_dir,
                                                 run_type=run_type, stored_pipeline_loc=pipeline_folder,
                                                 generate_automl_pipelines=run_baselines)
        experimenter_driver.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-type", '-r', help="How to run the driver.  'all' generates and executes, 'execute' "
                                                 "only executes pipelines from the database, 'pipeline_path' "
                                                 "executes pipelines from a specific folder and 'generate' only "
                                                 "creates pipelines and stores them in the database",
                        choices=["all", "execute", "generate", "pipeline_path", "distribute", "baselines"], default="all")
    parser.add_argument("--pipeline-folder", '-f', help="The path of the folder containing/to receive the pipelines")
    parser.add_argument("--run-baselines", '-b', help="Whether or not to exclusively run automl system pipelines",
                        action='store_true')
    parser.add_argument("--run-custom-fit", '-c', help="Whether or not to run only fit and use given pipelines",
                        action='store_true')
    parser.add_argument("--verbose", "-v", action="store_true", help="Whether to print for debugging or not", default=False)
    args = parser.parse_args()
    main(args.run_type, args.pipeline_folder, args.run_baselines, args.run_custom_fit)
