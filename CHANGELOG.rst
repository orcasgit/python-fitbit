0.3.1 (2019-05-24)
==================
* Fix auth with newer versions of OAuth libraries while retaining backward compatibility

0.3.0 (2017-01-24)
==================
* Surface errors better
* Use requests-oauthlib auto refresh to automatically refresh tokens if possible

0.2.4 (2016-11-10)
==================
* Call a hook if it exists when tokens are refreshed

0.2.3 (2016-07-06)
==================
* Refresh token when it expires

0.2.2 (2016-03-30)
==================
* Refresh token bugfixes

0.2.1 (2016-03-28)
==================
* Update requirements to use requests-oauthlib>=0.6.1

0.2 (2016-03-23)
================

* Drop OAuth1 support. See `OAuth1 deprecated <https://dev.fitbit.com/docs/oauth2/#oauth-1-0a-deprecated>`_
* Drop py26 and py32 support

0.1.3 (2015-02-04)
==================

* Support Intraday Time Series API
* Use connection pooling to avoid a TCP and SSL handshake for every API call

0.1.2 (2014-09-19)
==================

* Quick fix for response objects without a status code

0.1.1 (2014-09-18)
==================

* Fix the broken foods log date endpoint
* Integrate with travis-ci.org, coveralls.io, and requires.io
* Add HTTPTooManyRequests exception with retry_after_secs information
* Enable adding parameters to authorize token URL

0.1.0 (2014-04-15)
==================

* Officially test/support Python 3.2+ and PyPy in addition to Python 2.x
* Clean up OAuth workflow, change the API slightly to match oauthlib terminology
* Fix some minor bugs

0.0.5 (2014-03-30)
==================

* Switch from python-oauth2 to the better supported oauthlib
* Add get_bodyweight and get_bodyfat methods

0.0.3 (2014-02-05)
==================

* Add get_badges method
* Include error messages in the exception
* Add API for alarms
* Add API for log activity
* Correctly pass headers on requests
* Way more test coverage
* Publish to PyPI

0.0.2 (2012-10-02)
==================

* Add docs, including Readthedocs support
* Add tests
* Use official oauth2 version from pypi

0.0.1 (2012-02-25)
==================

* Initial release
