#!/usr/bin/env python
"""
This was taken, and modified from python-oauth2/example/client.py,
License reproduced below.

--------------------------
The MIT License

Copyright (c) 2007 Leah Culver

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Example consumer. This is not recommended for production.
Instead, you'll want to create your own subclass of OAuthClient
or find one that works with your web framework.
"""

import os
import pprint
import sys
import webbrowser

from fitbit.api import FitbitOauthClient


def gather_keys():
    # setup
    pp = pprint.PrettyPrinter(indent=4)
    print('** OAuth Python Library Example **\n')
    client = FitbitOauthClient(CLIENT_KEY, CLIENT_SECRET)

    # get request token
    print('* Obtain a request token ...\n')
    token = client.fetch_request_token()
    print('RESPONSE')
    pp.pprint(token)
    print('')

    print('* Authorize the request token in your browser\n')
    stderr = os.dup(2)
    os.close(2)
    os.open(os.devnull, os.O_RDWR)
    webbrowser.open(client.authorize_token_url())
    os.dup2(stderr, 2)
    try:
        verifier = raw_input('Verifier: ')
    except NameError:
        # Python 3.x
        verifier = input('Verifier: ')

    # get access token
    print('\n* Obtain an access token ...\n')
    token = client.fetch_access_token(verifier)
    print('RESPONSE')
    pp.pprint(token)
    print('')


if __name__ == '__main__':
    if not (len(sys.argv) == 3):
        print("Arguments 'client key', 'client secret' are required")
        sys.exit(1)
    CLIENT_KEY = sys.argv[1]
    CLIENT_SECRET = sys.argv[2]

    gather_keys()
    print('Done.')
