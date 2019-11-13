FROM registry.gitlab.com/datadrivendiscovery/images/primitives:ubuntu-bionic-python36-v2019.6.7
# TODO: Once the `fix-imputer` branch of our d3m-primitives repo
# has been merged and the package re-released to pypi, we can
# change this to reflect the pypi version. Once the new pypi
# version is on the d3m docker image, we can remove this line
# completely.
RUN git clone --single-branch --branch fix-imputer https://github.com/byu-dml/d3m-primitives.git
RUN pip3 install -e ./d3m-primitives
# RUN pip3 install -e git+https://github.com/byu-dml/d3m-primitives.git@fix-imputer#egg=byudml
# TODO: Once the newest dsbox gets added to the new docker container and we
# update docker containers, we can remove this install.
RUN pip3 install -e git+https://github.com/usc-isi-i2/dsbox-primitives.git@master#egg=dsbox
ADD . /d3m-experimenter
WORKDIR /d3m-experimenter
RUN pip3 install -r requirements.txt
