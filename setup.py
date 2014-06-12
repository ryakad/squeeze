#! /usr/bin/env python
#
# Git Squeeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Python Package Setup File
#
# Author: Ryan Kadwell <ryan@riaka.ca>
#

from setuptools import setup
# from pip.req import parse_requirements
from os import path

# # Fetch the list of requirements from the requirements.txt file
# requirements = parse_requirements(
#    path.abspath(os.path.dirname(path.abspath(__file__)) + "requirements.txt")
#    )


setup(
   name='gitsqueeze',
   version='alpha',
   author='Ryan Kadwell',
   author_email='ryan@riaka.ca',
   packages=['gitsqueeze'],
   scripts=["bin/git-squeeze"],
   url='http://pypi.python.org/pypi/GitSqueeze/',
   license='LICENSE.txt',
   description='Hook into git changesets',
   long_description=open('README.md').read(),
   # install_requires=[str(ir.req) for ir in requirements]
   install_requires=["logbook>=0.7.0", "psutil>=2.1.0"],
)
