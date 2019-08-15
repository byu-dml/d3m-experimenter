FROM registry.datadrivendiscovery.org/jpl/docker_images/complete:ubuntu-artful-python36-v2019.2.18-20190303-060946
ADD $EXPERIMENTER /d3m-experimenter
WORKDIR /d3m-experimenter
RUN echo $REQS
RUN ABC=requirements.txt
RUN echo $REQS$ABC
RUN pip3 install -r $REQS$ABC
