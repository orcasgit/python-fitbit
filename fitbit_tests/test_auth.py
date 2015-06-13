from unittest import TestCase
from fitbit import Fitbit, FitbitOauthClient, FitbitOauth2Client
import mock
from requests_oauthlib import OAuth1Session, OAuth2Session
from oauthlib.oauth2 import TokenExpiredError

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

    def test_authorize_token_url_with_parameters(self):
        # authorize_token_url calls oauth and returns a URL
        client = FitbitOauthClient(**self.client_kwargs)
        retval = client.authorize_token_url(display="touch")
        self.assertTrue("display=touch" in retval)

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


class Auth2Test(TestCase):
    """Add tests for auth part of API
    mock the oauth library calls to simulate various responses,
    make sure we call the right oauth calls, respond correctly based on the responses
    """
    client_kwargs = {
        'client_key': 'fake_id',
        'client_secret': 'fake_secret',
        'callback_uri': 'fake_callback_url',
        'oauth2': True,
        'scope': ['fake_scope1']
    }
    def test_authorize_token_url(self):
        # authorize_token_url calls oauth and returns a URL
        fb = Fitbit(**self.client_kwargs)
        retval = fb.client.authorize_token_url()
        self.assertEqual(retval[0],'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=fake_id&scope=activity+nutrition+heartrate+location+nutrition+profile+settings+sleep+social+weight&state='+retval[1])

    def test_authorize_token_url_with_parameters(self):
        # authorize_token_url calls oauth and returns a URL
        fb = Fitbit(**self.client_kwargs)
        retval = fb.client.authorize_token_url(scope=self.client_kwargs['scope'],
                                            callback_uri=self.client_kwargs['callback_uri'])
        self.assertEqual(retval[0],'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=fake_id&scope='+ str(self.client_kwargs['scope'][0])+ '&state='+retval[1]+'&callback_uri='+self.client_kwargs['callback_uri'])


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
        with mock.patch.object(OAuth2Session, 'post') as r:
            r.return_value = fake_response(200,'{"access_token": "fake_return_access_token", "scope": "fake_scope", "token_type": "Bearer", "refresh_token": "fake_return_refresh_token"}')
            retval = fb.client.refresh_token()
        self.assertEqual("fake_return_access_token", retval['access_token'])
        self.assertEqual("fake_return_refresh_token", retval['refresh_token'])


    def test_auto_refresh_token_exception(self):
        # test of auto_refersh with tokenExpired exception
        # 1. first call to _request causes a TokenExpired
        # 2. the token_refresh call is faked
        # 3. the second call to _request returns a valid value
        kwargs = self.client_kwargs
        kwargs['access_token'] = 'fake_access_token'
        kwargs['refresh_token'] = 'fake_refresh_token'

        fb = Fitbit(**kwargs)
        with mock.patch.object(FitbitOauth2Client, '_request') as r:
            r.side_effect = [TokenExpiredError, fake_response(200,'correct_response')]
            with mock.patch.object(OAuth2Session, 'post') as auth:
                auth.return_value = fake_response(200,'{"access_token": "fake_return_access_token", "scope": "fake_scope", "token_type": "Bearer", "refresh_token": "fake_return_refresh_token"}')
                retval = fb.client.make_request(Fitbit.API_ENDPOINT + '/1/user/-/profile.json')
        self.assertEqual("correct_response", retval.text)
        self.assertEqual("fake_return_access_token", fb.client.token['access_token'])
        self.assertEqual("fake_return_refresh_token", fb.client.token['refresh_token'])
        self.assertEqual(1, auth.call_count)
        self.assertEqual(2, r.call_count)


    def test_auto_refresh_token_nonException(self):
        # test of auto_refersh when the exception doesn't fire
        # 1. first call to _request causes a 401 expired token response
        # 2. the token_refresh call is faked
        # 3. the second call to _request returns a valid value
        kwargs = self.client_kwargs
        kwargs['access_token'] = 'fake_access_token'
        kwargs['refresh_token'] = 'fake_refresh_token'

        fb = Fitbit(**kwargs)
        with mock.patch.object(FitbitOauth2Client, '_request') as r:
            r.side_effect = [fake_response(401,b'{"errors": [{"message": "Access token invalid or expired: some_token_goes_here", "errorType": "oauth", "fieldName": "access_token"}]}'),
                             fake_response(200,'correct_response')]
            with mock.patch.object(OAuth2Session, 'post') as auth:
                auth.return_value = fake_response(200,'{"access_token": "fake_return_access_token", "scope": "fake_scope", "token_type": "Bearer", "refresh_token": "fake_return_refresh_token"}')
                retval = fb.client.make_request(Fitbit.API_ENDPOINT + '/1/user/-/profile.json')
        self.assertEqual("correct_response", retval.text)
        self.assertEqual("fake_return_access_token", fb.client.token['access_token'])
        self.assertEqual("fake_return_refresh_token", fb.client.token['refresh_token'])
        self.assertEqual(1, auth.call_count)
        self.assertEqual(2, r.call_count)


class fake_response(object):
    def __init__(self,code,text):
        self.status_code = code
        self.text = text
        self.content = text 
