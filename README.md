# Overview

The D3M Experimenter is a distributed system for running machine learning (ML) pipelines built on top of [D3M ecosystem](https://docs.datadrivendiscovery.org/).
The results of running each pipeline on a dataset are stored in the [D3M Metalearning Database](https://metalearning.datadrivendiscovery.org/).

## Getting Started

Running the D3M Experimenter requires [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/).

## Usage

Services are managed with [Docker Swarm](https://docs.docker.com/engine/swarm/).
Before running the D3M experimenter, you must setup a [`.env` configuration file](https://docs.docker.com/compose/environment-variables/#the-env-file) that will be used with `docker-compose`.

### Environment Configuration

Copy `.env-example` to `.env` and set the appropriate values for each environment variable.
At the very least, `DATASETS_DIR`, `EXPERIMENTER_DIR`, and `DATA_DIR` must be set.
* `DATASETS_DIR` is the absolute path to a directory containing dataset
* `EXPERIMENTER_DIR` is the absolute to the root of this repository on your host machine
* `DATA_DIR` is the absolute path to a directory where the D3M experimenter can write files

### Running the Swarm

First, [build](https://docs.docker.com/engine/reference/commandline/build/) the local images using (from the root of the repository):

```bash
sudo docker build --tag d3m-experimenter .
```

Next, creat the [docker swarm](https://docs.docker.com/engine/swarm/swarm-tutorial/create-swarm/):

```bash
sudo docker swarm init --advertise-addr <host ip address>
```

More nodes can be added to the swarm using (this is output by the above command):

```bash
sudo docker swarm join --token <token> <host>:<port>
```

Finally, [deploy](https://docs.docker.com/engine/swarm/stack-deploy/) the D3M Experimenter to the swarm:

```bash
sudo docker-compose config | sudo docker stack deploy --compose-file - <stack-name>
```

The services listed in [docker-compose.yml](docker-compose.yml) can be [scaled](https://docs.docker.com/engine/swarm/swarm-tutorial/scale-service/) to have more [replicas](https://docs.docker.com/engine/swarm/how-swarm-mode-works/services/) using:

```bash
sudo docker service scale <service-id>=<number-of-tasks>
```

Service IDs can be obtained from a manager node using

```bash
sudo docker service ls
```

The swarm can be taken down by removing all nodes from the swarm:

```bash
sudo docker swarm leave [--force]
```

### Development

To run code inside the swarm, there is a `dev` service.
This repository is mounted as a `read_only` volume by specifying its path on your host machine in the `.env` file.
First get the running container's ID and attach to it using:

```bash
sudo docker ps -f name=dev --quiet
sudo docker exec -it <dev-container-ID> bash
```
