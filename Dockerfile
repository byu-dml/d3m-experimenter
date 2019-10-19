FROM registry.gitlab.com/datadrivendiscovery/images/primitives:ubuntu-bionic-python36-v2019.6.7
ADD . /d3m-experimenter
RUN pip3 install -r /d3m-experimenter/requirements.txt
WORKDIR /d3m-experimenter
