FROM registry.datadrivendiscovery.org/jpl/docker_images/complete:ubuntu-artful-python36-v2019.2.18-20190303-060946
ADD $EXPERIMENTER /d3m-experimenter
WORKDIR /d3m-experimenter
RUN pip3 install -r requirements.txt
