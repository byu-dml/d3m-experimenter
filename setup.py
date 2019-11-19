from setuptools import setup

with open('requirements.txt', 'r') as f:
    install_requires = list()
    for line in f:
        re = line.strip()
        if re:
            install_requires.append(re)

setup(
    name='d3mexperimenter',
    version='1.0',
    description='Package for building and running D3M experiments',
    author='BYU DML',
    # Just one author of many
    author_email='evanpeterson17@gmail.com',
    url='https://github.com/byu-dml/d3m-experimenter',
    packages=['experimenter'],
    python_requires='>=3.6',
    install_requires=install_requires,
)
