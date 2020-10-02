FROM registry.gitlab.com/datadrivendiscovery/images/primitives:ubuntu-bionic-python36-stable
ADD . /d3m-experimenter
WORKDIR /d3m-experimenter
RUN pip3 install -r requirements.txt
