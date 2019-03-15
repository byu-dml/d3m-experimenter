#! /bin/bash

pip3 install coverage &&\
coverage run --branch --source=experimenter,tests run_tests.py &&\
coverage report -m
