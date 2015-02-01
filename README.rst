python-fitbit
=============

.. image:: https://travis-ci.org/orcasgit/python-fitbit.svg?branch=master
   :target: https://travis-ci.org/orcasgit/python-fitbit
   :alt: Build Status
.. image:: https://coveralls.io/repos/orcasgit/python-fitbit/badge.png?branch=master
   :target: https://coveralls.io/r/orcasgit/python-fitbit?branch=master
   :alt: Coverage Status
.. image:: https://requires.io/github/orcasgit/python-fitbit/requirements.png?branch=master
   :target: https://requires.io/github/orcasgit/python-fitbit/requirements/?branch=master
   :alt: Requirements Status

Fitbit API Python Client Implementation

For documentation: `http://python-fitbit.readthedocs.org/ <http://python-fitbit.readthedocs.org/>`_

Requirements
============

* Python 2.6+
* [python-dateutil](https://pypi.python.org/pypi/python-dateutil/2.4.0) (always)
* [requests-oauthlib](https://pypi.python.org/pypi/requests-oauthlib) (always)
* [Sphinx](https://pypi.python.org/pypi/Sphinx) (to create the documention)
* [tox](https://pypi.python.org/pypi/tox) (for running the tests)
* [coverage](https://pypi.python.org/pypi/coverage/) (to create test coverage reports)

To use the library, you need to install the run time requirements:

   sudo pip install -r requirements/base.txt

To modify and test the library, you need to install the developer requirements:

   sudo pip install -r requirements/dev.txt

To run the library on a continuous integration server, you need to install the test requirements:

   sudo pip install -r requirements/test.txt
