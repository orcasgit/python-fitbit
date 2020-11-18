#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from setuptools import setup

required = [line for line in open('requirements/base.txt').read().split("\n") if line != '']
required_test = [line for line in open('requirements/test.txt').read().split("\n") if not line.startswith("-r") and line != '']

fbinit = open('fitbit/__init__.py').read()
author = re.search("__author__ = '([^']+)'", fbinit).group(1)
author_email = re.search("__author_email__ = '([^']+)'", fbinit).group(1)
version = re.search("__version__ = '([^']+)'", fbinit).group(1)

setup(
    name='fitbit',
    version=version,
    description='Fitbit API Wrapper.',
    long_description=open('README.rst').read(),
    author=author,
    author_email=author_email,
    url='https://github.com/orcasgit/python-fitbit',
    packages=['fitbit'],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=["setuptools"] + required,
    license='Apache 2.0',
    test_suite='fitbit_tests.all_tests',
    tests_require=required_test,
    classifiers=(
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy'
    ),
)
