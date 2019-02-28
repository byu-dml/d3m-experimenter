FROM registry.datadrivendiscovery.org/jpl/docker_images/complete:ubuntu-artful-python36-v2019.2.12
ADD . /d3m-experimenter
WORKDIR /d3m-experimenter