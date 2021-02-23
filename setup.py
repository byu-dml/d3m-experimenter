from setuptools import setup, find_packages


setup(
    name='d3m-experimenter',
    version='0.1.0',
    description='An extension of the D3M machine learning framework for populating the metalearning database.',
    author='Brandon Schoenfeld, Evan Peterson, Orion Weller',
    url='https://github.com/byu-dml/d3m-experimenter',
    packages=find_packages(include=['experimenter']),
    python_requires='>=3.6,<4.0',
    install_requires=[
        'd3m',  # TODO: add version bounds
        'docker>=4.4.0<4.5.0',
        'mypy==0.812',
        'redis>=3.5.0<3.6.0',
        'rq>=1.7.0<1.8.0'
        'elasticsearch==7.11.0',
        'elasticsearch_dsl==7.3.0'
    ],
)
