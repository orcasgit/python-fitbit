#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fitbit

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

required = ['requests==0.10.1', 'python-dateutil==1.5']


setup(
    name='fitbit',
    version=fitbit.__version__,
    description='Fitbit API Wrapper.',
    long_description=open('README.rst').read(),
    author='Issac Kelly, ORCAS',
    author_email='issac@kellycreativetech.com',
    url='https://github.com/issackelly/python-fitbit',
    packages=['fitbit'],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=required,
    license='Apache 2.0',
    classifiers=(
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache 2.0',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
)
