python-fitbit
=============

.. image:: https://badge.fury.io/py/fitbit.svg
    :target: https://badge.fury.io/py/fitbit
.. image:: https://travis-ci.org/orcasgit/python-fitbit.svg?branch=master
   :target: https://travis-ci.org/orcasgit/python-fitbit
   :alt: Build Status
.. image:: https://coveralls.io/repos/orcasgit/python-fitbit/badge.png?branch=master
   :target: https://coveralls.io/r/orcasgit/python-fitbit?branch=master
   :alt: Coverage Status
.. image:: https://requires.io/github/orcasgit/python-fitbit/requirements.png?branch=master
   :target: https://requires.io/github/orcasgit/python-fitbit/requirements/?branch=master
   :alt: Requirements Status
.. image:: https://badges.gitter.im/orcasgit/python-fitbit.png
   :target: https://gitter.im/orcasgit/python-fitbit
   :alt: Gitter chat

Fitbit API Python Client Implementation

For documentation: `http://python-fitbit.readthedocs.org/ <http://python-fitbit.readthedocs.org/>`_

Requirements
============

* Python 2.7+
* `python-dateutil`_ (always)
* `requests-oauthlib`_ (always)
* `Sphinx`_ (to create the documention)
* `tox`_ (for running the tests)
* `coverage`_ (to create test coverage reports)

.. _python-dateutil: https://pypi.python.org/pypi/python-dateutil/2.4.0
.. _requests-oauthlib: https://pypi.python.org/pypi/requests-oauthlib
.. _Sphinx: https://pypi.python.org/pypi/Sphinx
.. _tox: https://pypi.python.org/pypi/tox
.. _coverage: https://pypi.python.org/pypi/coverage/

To use the library, you need to install the run time requirements:

   sudo pip install -r requirements/base.txt

To modify and test the library, you need to install the developer requirements:

   sudo pip install -r requirements/dev.txt

To run the library on a continuous integration server, you need to install the test requirements:

   sudo pip install -r requirements/test.txt
