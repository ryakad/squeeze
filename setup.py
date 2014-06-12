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

setup(
   name='git-squeeze',
   version='alpha',
   author='Ryan Kadwell',
   author_email='ryan@riaka.ca',
   packages=['gitsqueeze'],
   scripts=[],
   url='http://pypi.python.org/pypi/GitSqueeze/',
   license='LICENSE.txt',
   description='Hook into git changesets',
   long_description=open('README.md').read(),
   # install_requires=[
   #    "LogBook >= 0.7.0",
   # ],
)
