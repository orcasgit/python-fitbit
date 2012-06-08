#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

required = ['requests==0.10.1', 'python-dateutil==1.5']
fbinit = open('fitbit/__init__.py').read()
author = re.search("__author__ = '([^']+)'", fbinit).group(1)
version = re.search("__version__ = '([^']+)'", fbinit).group(1)

setup(
    name='fitbit',
    version=version,
    description='Fitbit API Wrapper.',
    long_description=open('README.rst').read(),
    author=author,
    author_email='issac@kellycreativetech.com',
    url='https://github.com/issackelly/python-fitbit',
    packages=['fitbit'],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=required,
    license='Apache 2.0',
    test_suite='tests.all_tests',
    classifiers=(
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache 2.0',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
)
