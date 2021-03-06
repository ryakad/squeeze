#! /usr/bin/env python
#
# Squeeze
# Copyright (c) Ryan Kadwell <ryan@riaka.ca>
#
# Python Package Setup File
#
# Author: Ryan Kadwell <ryan@riaka.ca>
#

from setuptools import setup

setup(
   name='squeeze',
   version='alpha',
   author='Ryan Kadwell',
   author_email='ryan@riaka.ca',
   packages=['squeeze'],
   scripts=["bin/squeeze"],
   # url='http://pypi.python.org/pypi/Squeeze/',
   license='LICENSE.txt',
   description='Library for parsing change sets from version control systems',
   long_description=open('README.md').read(),
   install_requires=[
      "logbook>=0.7.0",
      "psutil>=2.1.0",
      "PyYaml>=3.11"
   ]
)
