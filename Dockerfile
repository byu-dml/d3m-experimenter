FROM registry.gitlab.com/datadrivendiscovery/images/primitives:ubuntu-bionic-python36-devel
ADD . /d3m-experimenter
WORKDIR /d3m-experimenter
RUN pip3 install --no-cache .
