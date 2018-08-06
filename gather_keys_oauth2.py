#!/usr/bin/env python
import cherrypy
import os
import sys
import threading
import traceback
import webbrowser

from base64 import b64encode
from fitbit.api import Fitbit
from oauthlib.oauth2.rfc6749.errors import MismatchingStateError, MissingTokenError
import urllib.parse as urlparse
import argparse

class OAuth2Server:
    def __init__(self, client_id, client_secret,
                 redirect_uri='http://127.0.0.1:8080/'):
        """ Initialize the FitbitOauth2Client """
        self.success_html = """
            <h1>You are now authorized to access the Fitbit API!</h1>
            <br/><h3>You can close this window</h3>"""
        self.failure_html = """
            <h1>ERROR: %s</h1><br/><h3>You can close this window</h3>%s"""

        self.fitbit = Fitbit(
            client_id,
            client_secret,
            redirect_uri=redirect_uri,
            timeout=10,
        )

    def browser_authorize(self):
        """
        Open a browser to the authorization url and spool up a CherryPy
        server to accept the response
        """
        url, _ = self.fitbit.client.authorize_token_url()
        # Open the web browser in a new thread for command-line browser support
        threading.Timer(1, webbrowser.open, args=(url,)).start()
        cherrypy.quickstart(self)

    def headless_authorize(self):
        """
        Authorize without a display using only TTY.
        """
        url, _ = self.fitbit.client.authorize_token_url()
        # Ask the user to open this url on a system with browser
        print('\n-------------------------------------------------------------------------')
        print('\t\tOpen the below URL in your browser\n')
        print(url)
        print('\n-------------------------------------------------------------------------\n')
        print('NOTE: After authenticating on Fitbit website, you will redirected to a URL which ')
        print('throws an ERROR. This is expected! Just copy the full redirected here.\n')
        redirected_url = input('Full redirected URL: ')
        params = urlparse.parse_qs(urlparse.urlparse(redirected_url).query)
        print(params['code'][0])
        self.authenticate_code(code=params['code'][0])

    @cherrypy.expose
    def index(self, state, code=None, error=None):
        """
        Receive a Fitbit response containing a verification code. Use the code
        to fetch the access_token.
        """
        error = None
        if code:
            self.authenticate_code(code=code)
        else:
            error = self._fmt_failure('Unknown error while authenticating')
        # Use a thread to shutdown cherrypy so we can return HTML first
        self._shutdown_cherrypy()
        return error if error else self.success_html

    def _fmt_failure(self, message):
        tb = traceback.format_tb(sys.exc_info()[2])
        tb_html = '<pre>%s</pre>' % ('\n'.join(tb)) if tb else ''
        return self.failure_html % (message, tb_html)

    def authenticate_code(self, code=None):
        """
        Final stage of authentication using the code from Fitbit.
        """
        try:
            self.fitbit.client.fetch_access_token(code)
        except MissingTokenError:
            error = self._fmt_failure(
                'Missing access token parameter.</br>Please check that '
                'you are using the correct client_secret'
            )
        except MismatchingStateError:
            error = self._fmt_failure('CSRF Warning! Mismatching state')

    def _shutdown_cherrypy(self):
        """ Shutdown cherrypy in one second, if it's running """
        if cherrypy.engine.state == cherrypy.engine.states.STARTED:
            threading.Timer(1, cherrypy.engine.exit).start()


if __name__ == '__main__':

    # Arguments parsing
    parser = argparse.ArgumentParser("Client ID and Secret are mandatory arguments")
    parser.add_argument("-i", "--id", required=True, help="Client id", metavar='<client-id>')
    parser.add_argument("-s", "--secret", required=True, help="Client secret", 
        metavar='<client-secret>')
    parser.add_argument("-c", "--console", default=False, 
        help="Authenticate only using console (for headless systems)", action="store_true")
    args = parser.parse_args()

    server = OAuth2Server(args.id, args.secret)
    if args.console:
        server.headless_authorize()
    else:   
        server.browser_authorize()

    profile = server.fitbit.user_profile_get()
    print('You are authorized to access data for the user: {}'.format(
        profile['user']['fullName']))

    print('TOKEN\n=====\n')
    for key, value in server.fitbit.client.session.token.items():
        print('{} = {}'.format(key, value))
