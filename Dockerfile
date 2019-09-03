FROM registry.datadrivendiscovery.org/jpl/docker_images/complete:ubuntu-bionic-python36-v2019.6.7
ADD . /d3m-experimenter
WORKDIR /d3m-experimenter
RUN pip3 install -r requirements.txt
