from setuptools import setup, find_packages

with open('requirements.txt', 'r') as f:
    install_requires = list()
    for line in f:
        re = line.strip()
        if re:
            install_requires.append(re)

setup(
    name='d3m_experimenter',
    version='1.0',
    description='Package for building and running D3M experiments',
    author='BYU DML',
    # Just one author of many
    author_email='evanpeterson17@gmail.com',
    url='https://github.com/byu-dml/d3m-experimenter',
    packages=find_packages(include=['experimenter', 'experimenter.*']),
    python_requires='>=3.6',
    install_requires=install_requires,
)
