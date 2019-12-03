FROM registry.gitlab.com/datadrivendiscovery/images/primitives:ubuntu-bionic-python36-v2019.11.10-20191127-050901
ADD . /d3m-experimenter
WORKDIR /d3m-experimenter
RUN pip3 install -r requirements.txt
