.. Python-Fitbit documentation master file, created by
   sphinx-quickstart on Wed Mar 14 18:51:57 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Overview
========

This is a complete python implementation of the Fitbit API.

It uses oAuth for authentication, it supports both us and si
measurements

Quickstart
==========

If you are only retrieving data that doesn't require authorization, then you can use the unauthorized interface::

    import fitbit
    unauth_client = fitbit.Fitbit('<consumer_key>', '<consumer_secret>')
    # certain methods do not require user keys
    unauth_client.food_units()

Here is an example of authorizing with OAuth 2.0::

    # You'll have to gather the tokens on your own, or use
    # ./gather_keys_oauth2.py
    authd_client = fitbit.Fitbit('<consumer_key>', '<consumer_secret>',
                                 access_token='<access_token>', refresh_token='<refresh_token>')
    authd_client.sleep()

Fitbit API
==========

Some assumptions you should note. Anywhere it says user_id=None,
it assumes the current user_id from the credentials given, and passes
a ``-`` through the API.  Anywhere it says date=None, it should accept
either ``None`` or a ``date`` or ``datetime`` object
(anything with proper strftime will do), or a string formatted
as ``%Y-%m-%d``.

.. autoclass:: fitbit.Fitbit
    :private-members:
    :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
