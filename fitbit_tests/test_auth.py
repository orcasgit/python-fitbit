from unittest import TestCase
from fitbit import Fitbit
import mock
from requests_oauthlib import OAuth1Session

class AuthTest(TestCase):
    """Add tests for auth part of API
    mock the oauth library calls to simulate various responses,
    make sure we call the right oauth calls, respond correctly based on the responses
    """
    client_kwargs = {
        'client_key': '',
        'client_secret': '',
        'user_key': None,
        'user_secret': None,
        'callback_uri': 'CALLBACK_URL'
    }

    def test_fetch_request_token(self):
        # fetch_request_token needs to make a request and then build a token from the response

        fb = Fitbit(**self.client_kwargs)
        with mock.patch.object(OAuth1Session, 'fetch_request_token') as frt:
            frt.return_value = {
                'oauth_callback_confirmed': 'true',
                'oauth_token': 'FAKE_OAUTH_TOKEN',
                'oauth_token_secret': 'FAKE_OAUTH_TOKEN_SECRET'}
            retval = fb.client.fetch_request_token()
            self.assertEqual(1, frt.call_count)
            # Got the right return value
            self.assertEqual('true', retval.get('oauth_callback_confirmed'))
            self.assertEqual('FAKE_OAUTH_TOKEN', retval.get('oauth_token'))
            self.assertEqual('FAKE_OAUTH_TOKEN_SECRET',
                             retval.get('oauth_token_secret'))

    def test_authorize_token_url(self):
        # authorize_token_url calls oauth and returns a URL
        fb = Fitbit(**self.client_kwargs)
        with mock.patch.object(OAuth1Session, 'authorization_url') as au:
            au.return_value = 'FAKEURL'
            retval = fb.client.authorize_token_url()
            self.assertEqual(1, au.call_count)
            self.assertEqual("FAKEURL", retval)

    def test_fetch_access_token(self):
        kwargs = self.client_kwargs
        kwargs['resource_owner_key'] = ''
        kwargs['resource_owner_secret'] = ''
        fb = Fitbit(**kwargs)
        fake_verifier = "FAKEVERIFIER"
        with mock.patch.object(OAuth1Session, 'fetch_access_token') as fat:
            fat.return_value = {
                'encoded_user_id': 'FAKE_USER_ID',
                'oauth_token': 'FAKE_RETURNED_KEY',
                'oauth_token_secret': 'FAKE_RETURNED_SECRET'
            }
            retval = fb.client.fetch_access_token(fake_verifier)
        self.assertEqual("FAKE_RETURNED_KEY", retval['oauth_token'])
        self.assertEqual("FAKE_RETURNED_SECRET", retval['oauth_token_secret'])
        self.assertEqual('FAKE_USER_ID', fb.client.user_id)
