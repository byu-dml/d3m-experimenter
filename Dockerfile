FROM registry.gitlab.com/datadrivendiscovery/images/primitives:ubuntu-bionic-python36-v2019.6.7
# TODO: Once the `fix-imputer` branch of our d3m-primitives repo
# has been merged and the package re-released to pypi, we can
# change this to reflect the pypi version. Once the new pypi
# version is on the d3m docker image, we can remove this line
# completely.
RUN pip3 install -e git+https://github.com/byu-dml/d3m-primitives.git@fix-imputer#egg=byudml
ADD . /d3m-experimenter
WORKDIR /d3m-experimenter
RUN pip3 install -r requirements.txt
