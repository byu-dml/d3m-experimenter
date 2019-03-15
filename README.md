# Current State and Goals (as of 2.13.19)
1. It runs on all dataset types (seed, LL0, LL1).  It runs on classification (14 counts) and regression (17 counts) type problems that contain tabular data, as well as on many preprocessors (9 counts).
3. Future work includes hyper-parameter tuning and implementing ensembling methods

# Getting Started
### Repositories ###
* Clone the Experimenter Repo from [here](https://github.com/byu-dml/d3m-experimenter)
* Note that the directories used for these repositories will be the ones used in the docker-compose volumes

### docker-compose
Compose is a way to more easily run docker containers than the `docker run` command.
* Install docker-compose [here](https://docs.docker.com/compose/install/#install-compose) if you don't already have it installed.
* Copy the file `.env.example` and name the copy `.env`
  * Modify the value after`VOLUMES=` to whatever you want your container's docker volumes to be (the default is your home directory)
    * If you are planning on running the d3m runtime locally, make sure that you will have access to your cloned d3m repository
  * The volumes inside of the container can be accessed at the path `/volumes`
  * Make sure `DATASETS=` is pointing to the datasets you want the container to have access to
  * The datasets can be accessed from inside the container at `/datasets`
  * Fill in the values for connections to databases and host computers

# Usage
### Running the Container
Before being able to pull the image you will need to login the D3M's private docker registry.
* Run `sudo docker login registry.datadrivendiscovery.org` and follow the prompts to enter your username and password
* Run `sudo docker-compose up -d`
  * Note: If you get a permission denied error, try rerunning the command with `sudo`
  * Note: if you have previously installed a d3m docker image before and this one is not working, try using `sudo docker-compose build` and try these steps again
  * If you don't want to use `sudo` follow the instructions [here](https://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo)
* Run `docker exec -it experimenter bash` to access the container from the command line

Once inside the container you should be able to follow the instructions for d3m found [here](https://gitlab.com/datadrivendiscovery/d3m)
  * One example command is `python3 -m d3m.index search`. This will list all of the primitives inside of the container
  * Example of running a pipeline:
    * `python3 -m d3m.runtime -d /datasets -v /volumes fit-produce -m /volumes/.meta -p /volumes/pipelines/random-forest-classification.yml`
  
### Running Local D3M Runtime
* Option 1:
  * Run `pip3 uninstall d3m`
  * Run `pip3 install --process-dependency-links -e {path_to_your_d3m_repo}`
  * Now you should be running the local D3M runtime and any changes you make should be reflected when you run the code
* Option 2:
  * Run `sudo docker exec -it experimenter bash`
  * Change into where you mounted the d3m runtime code
  * Run d3m commands as you normally would, and it will use the local code
 

### Bringing Down the Container
* To stop and remove the container run `docker-compose down` from within the directory with the docker-compose.yml file


# How-To Run After Set-Up #
0. The steps in the subsections below have been completed.  The repos have been cloned and the docker image is instantiated.
1. Run the experimenter using the command: `python3 experimenter_driver.py`
2. The driver generates all possible problems from the list of problem directories given to it in constants.py
3. It uses the Experimenter class to generate all possible pipelines from lists of pipelines types.  These are generated in Experimenter.py but the models used are in constants.py
4. It runs all pipelines with all problems.
5. When a pipeline runs successfully, the driver writes a pipeline run file to the mongo_db specified in `database_communication.py`.  The default is a computer in our lab.
6. To see all the items in the database create a folder with the collection names as subdirectories. Then run `python3 get_documents.py`.  F
or specific db commands see `get_documents.py`.
7. The outputs from the above step will be placed in the directory passed into the command line OR the default location (currently the home directory)

## Run Options ##
* To generate and execute pipelines in one command run `python3 experimenter_driver.py` 
* To generate only pipelines and store them, run `python3 experimenter_driver.py -r generate`.  It will store them in the MongoDB.
* To run pipelines from mongodb and not generate new ones, run `python3 experimenter_driver.py -r execute`
* To only execute created pipelines stored in a folder, add the `-f folder_name/` flag.
* To distribute pipelines run `python3 experimenter_driver.py -r distribute`.
* To run AutoML systems for comparisons add the `-b` flag.  Note this will turn any command into ONLY executing AutoML systems
* For more information, see the documentation in `experimenter_driver.py`.


## Lab Distribution Options ##
1. Create jobs by runninng `python3 experimenter_driver.py -r distribute`.  This adds jobs to the RQ queue.
2. Join machines to the queue by using cssh (Clustered SSH). Install it, if it is not installed (`sudo apt-get install cssh`).
3. Execute the command `cssh` followed the by all the names of the machine you want it to run on.  For example `cssh lab1 lab2`
4. If you encounter an error about not being able to authenticate with the other machine, make sure you can regular SSH into it first and then try again.
5. To prep a lab computer to run this software, use `prep-machine.sh`.  Once that is run and you are in the Docker container run `build_env_and_work` to become a worker.

