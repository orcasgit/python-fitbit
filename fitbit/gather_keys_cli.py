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

from api import FitbitOauthClient
import time
import oauth2 as oauth
import urlparse
import platform
import subprocess



def gather_keys():
    # setup
    print '** OAuth Python Library Example **'
    client = FitbitOauthClient(CONSUMER_KEY, CONSUMER_SECRET)

    print ''

    # get request token
    print '* Obtain a request token ...'
    print ''
    token = client.fetch_request_token()
    print 'FROM RESPONSE'
    print 'key: %s' % str(token.key)
    print 'secret: %s' % str(token.secret)
    print 'callback confirmed? %s' % str(token.callback_confirmed)
    print ''

    print '* Authorize the request token in your browser'
    print ''
    if platform.mac_ver():
        subprocess.Popen(['open', client.authorize_token_url(token)])
    else:
        print 'open: %s' % client.authorize_token_url(token)
    print ''
    verifier = raw_input('Verifier: ')
    print verifier
    print ''

    # get access token
    print '* Obtain an access token ...'
    print ''
    print 'REQUEST (via headers)'
    print ''
    token = client.fetch_access_token(token, verifier)
    print 'FROM RESPONSE'
    print 'key: %s' % str(token.key)
    print 'secret: %s' % str(token.secret)
    print ''


def pause():
    print ''
    time.sleep(1)

if __name__ == '__main__':
    import sys

    if not (len(sys.argv) == 3):
        print "Arguments 'client key', 'client secret' are required"
        sys.exit(1)
    CONSUMER_KEY = sys.argv[1]
    CONSUMER_SECRET = sys.argv[2]

    gather_keys()
    print 'Done.'
