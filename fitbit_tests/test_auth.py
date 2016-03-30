from unittest import TestCase
from fitbit import Fitbit, FitbitOauth2Client
from fitbit.exceptions import HTTPUnauthorized
import mock
from requests_oauthlib import OAuth2Session


class Auth2Test(TestCase):
    """Add tests for auth part of API
    mock the oauth library calls to simulate various responses,
    make sure we call the right oauth calls, respond correctly based on the
    responses
    """
    client_kwargs = {
        'client_id': 'fake_id',
        'client_secret': 'fake_secret',
        'callback_uri': 'fake_callback_url',
        'scope': ['fake_scope1']
    }

    def test_authorize_token_url(self):
        # authorize_token_url calls oauth and returns a URL
        fb = Fitbit(**self.client_kwargs)
        retval = fb.client.authorize_token_url()
        self.assertEqual(retval[0], 'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=fake_id&scope=activity+nutrition+heartrate+location+nutrition+profile+settings+sleep+social+weight&state='+retval[1])

    def test_authorize_token_url_with_parameters(self):
        # authorize_token_url calls oauth and returns a URL
        fb = Fitbit(**self.client_kwargs)
        retval = fb.client.authorize_token_url(
            scope=self.client_kwargs['scope'],
            callback_uri=self.client_kwargs['callback_uri'])
        self.assertEqual(retval[0], 'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=fake_id&scope='+ str(self.client_kwargs['scope'][0])+ '&state='+retval[1]+'&callback_uri='+self.client_kwargs['callback_uri'])

    def test_fetch_access_token(self):
        # tests the fetching of access token using code and redirect_URL
        fb = Fitbit(**self.client_kwargs)
        fake_code = "fake_code"
        with mock.patch.object(OAuth2Session, 'fetch_token') as fat:
            fat.return_value = {
                'access_token': 'fake_return_access_token',
                'refresh_token': 'fake_return_refresh_token'
            }
            retval = fb.client.fetch_access_token(fake_code, self.client_kwargs['callback_uri'])
        self.assertEqual("fake_return_access_token", retval['access_token'])
        self.assertEqual("fake_return_refresh_token", retval['refresh_token'])

    def test_refresh_token(self):
        # test of refresh function
        kwargs = self.client_kwargs
        kwargs['access_token'] = 'fake_access_token'
        kwargs['refresh_token'] = 'fake_refresh_token'
        fb = Fitbit(**kwargs)
        with mock.patch.object(OAuth2Session, 'refresh_token') as rt:
            rt.return_value = {
                'access_token': 'fake_return_access_token',
                'refresh_token': 'fake_return_refresh_token'
            }
            retval = fb.client.refresh_token()
        self.assertEqual("fake_return_access_token", retval['access_token'])
        self.assertEqual("fake_return_refresh_token", retval['refresh_token'])

    def test_auto_refresh_token_exception(self):
        """Test of auto_refresh with Unauthorized exception"""
        # 1. first call to _request causes a HTTPUnauthorized
        # 2. the token_refresh call is faked
        # 3. the second call to _request returns a valid value
        kwargs = self.client_kwargs
        kwargs['access_token'] = 'fake_access_token'
        kwargs['refresh_token'] = 'fake_refresh_token'

        fb = Fitbit(**kwargs)
        with mock.patch.object(FitbitOauth2Client, '_request') as r:
            r.side_effect = [
                HTTPUnauthorized(fake_response(401, b'correct_response')),
                fake_response(200, 'correct_response')
            ]
            with mock.patch.object(OAuth2Session, 'refresh_token') as rt:
                rt.return_value = {
                    'access_token': 'fake_return_access_token',
                    'refresh_token': 'fake_return_refresh_token'
                }
                retval = fb.client.make_request(Fitbit.API_ENDPOINT + '/1/user/-/profile.json')
        self.assertEqual("correct_response", retval.text)
        self.assertEqual(
            "fake_return_access_token", fb.client.token['access_token'])
        self.assertEqual(
            "fake_return_refresh_token", fb.client.token['refresh_token'])
        self.assertEqual(1, rt.call_count)
        self.assertEqual(2, r.call_count)

    def test_auto_refresh_token_non_exception(self):
        """Test of auto_refersh when the exception doesn't fire"""
        # 1. first call to _request causes a 401 expired token response
        # 2. the token_refresh call is faked
        # 3. the second call to _request returns a valid value
        kwargs = self.client_kwargs
        kwargs['access_token'] = 'fake_access_token'
        kwargs['refresh_token'] = 'fake_refresh_token'

        fb = Fitbit(**kwargs)
        with mock.patch.object(FitbitOauth2Client, '_request') as r:
            r.side_effect = [
                fake_response(401, b'{"errors": [{"message": "Access token expired: some_token_goes_here", "errorType": "expired_token", "fieldName": "access_token"}]}'),
                fake_response(200, 'correct_response')
            ]
            with mock.patch.object(OAuth2Session, 'refresh_token') as rt:
                rt.return_value = {
                    'access_token': 'fake_return_access_token',
                    'refresh_token': 'fake_return_refresh_token'
                }
                retval = fb.client.make_request(Fitbit.API_ENDPOINT + '/1/user/-/profile.json')
        self.assertEqual("correct_response", retval.text)
        self.assertEqual(
            "fake_return_access_token", fb.client.token['access_token'])
        self.assertEqual(
            "fake_return_refresh_token", fb.client.token['refresh_token'])
        self.assertEqual(1, rt.call_count)
        self.assertEqual(2, r.call_count)


class fake_response(object):
    def __init__(self, code, text):
        self.status_code = code
        self.text = text
        self.content = text
