[![Build Status](https://api.travis-ci.org/byu-dml/d3m-experimenter.png)](https://travis-ci.org/byu-dml/d3m-experimenter)

# Overview

This package uses the [D3M ecosystem](https://docs.datadrivendiscovery.org/) for machine learning (ML) to build and execute ML pipelines on problems/datasets, storing the pipelines and results of the pipeline runs in a database. As such, this package is useful for generating meta-datasets for use in metalearning, among other things. It can run on all internal D3M dataset types (seed, LL0, LL1).  It runs on classification and regression problems that contain tabular data. It can use 15 classifiers, 17 regressors, and 11 preprocessors to build pipelines with. Future work includes hyper-parameter tuning.

# Getting Started

### Clone the repo

```shell
git clone https://github.com/byu-dml/d3m-experimenter
cd d3m-experimenter
```
Note: The directory the repo is cloned to will need to be supplied as a volume in `docker-compose.yml`.

### Setting the Docker Environment

`docker-compose` is a way to more easily run docker containers than the `docker run` command and is needed for this repo. Install `docker-compose` [here](https://docs.docker.com/compose/install/#install-compose) if you don't already have it installed.

Next copy the file `.env.example` and name the copy `.env` then make these modifications:

1. Make sure `DATASETS=` is pointing to the datasets you want the container to have access to. The datasets can then be accessed from inside the container at `/datasets`.
1. Modify `EXPERIMENTER=` to point to the root directory of this cloned repo.
1. Fill in the values for connections to the local Mongo database and Redis server, and to D3M's database.

# Usage

## Running the Container

In order for the experimenter to execute correctly and have access to machine learning primitives, it needs to run inside the repo's docker container, which is a "subclass" of the public D3M primitives container.

1.  First build, (re)create, and start the docker container:

    ```shell
    sudo docker-compose up -d
    ```
    Note: If you get a permission denied error, try rerunning the command with `sudo`. Another note: if you have previously installed a d3m docker image before and this one is not working, try using `sudo docker-compose build` then try these steps again.

    If you don't want to use `sudo` follow the instructions [here](https://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo).

1.  Next, access the container from the command line:
    ```shell
    sudo docker exec -it experimenter bash
    ```
    From within this command line you can execute the repo or use the [core d3m package](https://gitlab.com/datadrivendiscovery/d3m).


## Bringing Down the Container

To stop and remove the container run this command from within the directory with the `docker-compose.yml` file:

```shell
sudo docker-compose down
```

## Running The D3M Core Package

Inside the docker container you can use the d3m core package directly. One example command is `python3 -m d3m.index search`. This will list all of the primitives available inside the container.

An example of running a pipeline is:

```shell
python3 -m d3m.runtime -d /datasets -v /volumes fit-produce -m /volumes/.meta -p /volumes/pipelines/random-forest-classification.yml
```

This uses the d3m reference runtime to execute the pipeline described by `random-forest-classification.yml` on the datasets found at `/datasets`. More info on using d3m to run pipelines can be found [here](https://docs.datadrivendiscovery.org/devel/pipeline.html#reference-runtime).
  
### Running A Local Version of The D3M Runtime

To run a locally installed version of the d3m core package repo instead of the pypi version (useful when debugging d3m), there are two options:

*   **Option 1**: From inside the docker container command line:

    ```
    pip3 uninstall d3m
    pip3 install --process-dependency-links -e <path_to_your_d3m_repo>
    ```
    Now you should be running the local D3M runtime and any changes you make should be reflected when you run the code.

*   **Option 2**:
    From inside the docker container command line, change into where you mounted the locally installed d3m repo, then run d3m commands as you normally would, and it will use the local code.

## Running the Experimenter

Before using the experimenter, ensure the repo has been cloned, the docker image is instantiated, and you are inside the docker container's command line.

The core API of the repo is a CLI interface used for building and running pipelines, and for persisting those piplines and pipeline runs in a database. To see the CLI's documentation and default argument values:

```shell
python3 experimenter_driver.py --help
```

Some basic facts about the experimenter driver:

*   The driver generates all possible problems from the list of problem directories given to it in constants.py
*   It uses the `Experimenter` class to generate all possible pipelines from lists of pipelines types.  These are generated in Experimenter.py but the models used are in `constants.py`.
*   For each problem type (e.g. classification, regression), it runs all pipelines of that problem type with all problems of that problem type.
*   When a pipeline runs successfully, the driver writes a pipeline run file to the MongoDB instance specified in the `.env` file.  The default is a computer in our lab.

The most basic way to run the experimenter is:

```shell
python3 experimenter_driver.py
```

### Run Options

*   To generate and execute pipelines in one command run `python3 experimenter_driver.py` 
*   To generate pipelines but not execute them, run `python3 experimenter_driver.py --run-type generate`. This will store them in the MongoDB as well.
*   To run pipelines from mongodb and not generate new ones, run `python3 experimenter_driver.py --run-type execute`
*   To only execute created pipelines stored in a folder, add the `--pipeline-folder path/to/pipeline/folder` flag.
*   To distribute pipelines for concurrent execution run `python3 experimenter_driver.py --run-type distribute` (see "Lab Distribution Options" below for more info).
*   For more information, see the documentation in `experimenter_driver.py`.

### Lab Distribution Options

The repo can use a task queue to store pipelines on, with multiple machines acting in tandem to execute those pipelines and store them in the database.

#### Creating Jobs

To create jobs on the task queue:

```shell
python3 experimenter_driver.py --run-type distribute
```

This pulls all the pipelines out of the database and adds them to the RQ queue as jobs to be executed by workers.

#### Running Jobs

1.  Join machines to the queue as workers by using `clusterssh`. Install it, if it is not installed (`sudo apt-get install clusterssh`). A tutorial for using `clusterssh` can be found [here](https://www.linux.com/tutorials/managing-multiple-linux-servers-clusterssh/).
1.  Execute the command `cssh` followed by all the names of the machine you want it to run on.  For example `cssh lab1 lab2`. If you encounter an error about not being able to authenticate with the other machine, make sure you can regular SSH into it first and then try again.
1.  To prep a lab computer that has not already been set up to run as a worker, first clone the repo onto that computer, change into it, then run `prep-machine.sh`.  Once that is run and you are in the Docker container run `python3 rq-worker.py` to become a worker. Being a worker means that machine will take jobs (pipelines) off the RQ queue, execute them, and persist the resulting pipeline runs in the database. Note: This step can be executed in parallel on all workers from the `clusterssh` terminal.

### Accessing the DB

There are some helpers for easily viewing data in the database. To see all the items in the database create a folder with the collection names as subdirectories. Then run:

```shell
python3 get_documents.py
```

For specific DB commands see `get_documents.py`. The outputs from the above step will be placed in the directory passed into the command line OR the default location (currently the home directory).

# Contributing

## Random Numbers

For reproducibility, when using random numbers in the repo, use the `random_seed` variable importable from `experimenter.config` to seed your random number generator. If you are using the native `random` python package, you can import `random` from `experimenter.config`. It is a version of the `random` package that's already been seeded with the repo's shared seed. If you want the tests to run deterministically, supply an environment variable called `SEED` with the same value each time. The repo will then use that value as its common random seed.

## Managing The Database & Redis Queue

To start the database (only applies to the BYU DML lab):

```shell
ssh 1potato
cd /path/to/database_docker_compose_file/
sudo docker-compose up -d
```

To start up the Redis queue (also only applies to the BYU DML lab):

```shell
ssh 1potato
bash start_redis_rq.sh
```

To view the Redis queue dashboard, navigate your browser to `localhost:9181`.

**Note**: you may need to source the `REDIS_PORT`, `REDIS_DATA`, and `REDIS_HOST` environment variables from your `.env` file to get the `start_redis_rq.sh` script to run.
