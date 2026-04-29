from setuptools import find_packages
from setuptools import setup

setup(
    name='interfaces',
    version='0.0.1',
    packages=find_packages(
        include=('interfaces', 'interfaces.*')),
)
