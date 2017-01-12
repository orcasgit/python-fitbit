import copy
import json
import mock
import requests_mock

from datetime import datetime
from freezegun import freeze_time
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from requests.auth import _basic_auth_str
from unittest import TestCase

from fitbit import Fitbit


class Auth2Test(TestCase):
    """Add tests for auth part of API
    mock the oauth library calls to simulate various responses,
    make sure we call the right oauth calls, respond correctly based on the
    responses
    """
    client_kwargs = {
        'client_id': 'fake_id',
        'client_secret': 'fake_secret',
        'redirect_uri': 'http://127.0.0.1:8080',
        'scope': ['fake_scope1']
    }

    def test_authorize_token_url(self):
        # authorize_token_url calls oauth and returns a URL
        fb = Fitbit(**self.client_kwargs)
        retval = fb.client.authorize_token_url()
        self.assertEqual(retval[0], 'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=fake_id&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080&scope=activity+nutrition+heartrate+location+nutrition+profile+settings+sleep+social+weight&state='+retval[1])

    def test_authorize_token_url_with_scope(self):
        # authorize_token_url calls oauth and returns a URL
        fb = Fitbit(**self.client_kwargs)
        retval = fb.client.authorize_token_url(scope=self.client_kwargs['scope'])
        self.assertEqual(retval[0], 'https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=fake_id&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080&scope='+ str(self.client_kwargs['scope'][0])+ '&state='+retval[1])

    def test_fetch_access_token(self):
        # tests the fetching of access token using code and redirect_URL
        fb = Fitbit(**self.client_kwargs)
        fake_code = "fake_code"
        with requests_mock.mock() as m:
            m.post(fb.client.access_token_url, text=json.dumps({
                'access_token': 'fake_return_access_token',
                'refresh_token': 'fake_return_refresh_token'
            }))
            retval = fb.client.fetch_access_token(fake_code)
        self.assertEqual("fake_return_access_token", retval['access_token'])
        self.assertEqual("fake_return_refresh_token", retval['refresh_token'])

    def test_refresh_token(self):
        # test of refresh function
        kwargs = copy.copy(self.client_kwargs)
        kwargs['access_token'] = 'fake_access_token'
        kwargs['refresh_token'] = 'fake_refresh_token'
        kwargs['refresh_cb'] = lambda x: None
        fb = Fitbit(**kwargs)
        with requests_mock.mock() as m:
            m.post(fb.client.refresh_token_url, text=json.dumps({
                'access_token': 'fake_return_access_token',
                'refresh_token': 'fake_return_refresh_token'
            }))
            retval = fb.client.refresh_token()
        self.assertEqual("fake_return_access_token", retval['access_token'])
        self.assertEqual("fake_return_refresh_token", retval['refresh_token'])

    @freeze_time(datetime.fromtimestamp(1483563319))
    def test_auto_refresh_expires_at(self):
        """Test of auto_refresh with expired token"""
        # 1. first call to _request causes a HTTPUnauthorized
        # 2. the token_refresh call is faked
        # 3. the second call to _request returns a valid value
        refresh_cb = mock.MagicMock()
        kwargs = copy.copy(self.client_kwargs)
        kwargs.update({
            'access_token': 'fake_access_token',
            'refresh_token': 'fake_refresh_token',
            'expires_at': 1483530000,
            'refresh_cb': refresh_cb,
        })

        fb = Fitbit(**kwargs)
        profile_url = Fitbit.API_ENDPOINT + '/1/user/-/profile.json'
        with requests_mock.mock() as m:
            m.get(
                profile_url,
                text='{"user":{"aboutMe": "python-fitbit developer"}}',
                status_code=200
            )
            token = {
                'access_token': 'fake_return_access_token',
                'refresh_token': 'fake_return_refresh_token',
                'expires_at': 1483570000,
            }
            m.post(fb.client.refresh_token_url, text=json.dumps(token))
            retval = fb.make_request(profile_url)

        self.assertEqual(m.request_history[0].path, '/oauth2/token')
        self.assertEqual(
            m.request_history[0].headers['Authorization'],
            _basic_auth_str(
                self.client_kwargs['client_id'],
                self.client_kwargs['client_secret']
            )
        )
        self.assertEqual(retval['user']['aboutMe'], "python-fitbit developer")
        self.assertEqual("fake_return_access_token", token['access_token'])
        self.assertEqual("fake_return_refresh_token", token['refresh_token'])
        refresh_cb.assert_called_once_with(token)

    def test_auto_refresh_token_exception(self):
        """Test of auto_refresh with Unauthorized exception"""
        # 1. first call to _request causes a HTTPUnauthorized
        # 2. the token_refresh call is faked
        # 3. the second call to _request returns a valid value
        refresh_cb = mock.MagicMock()
        kwargs = copy.copy(self.client_kwargs)
        kwargs.update({
            'access_token': 'fake_access_token',
            'refresh_token': 'fake_refresh_token',
            'refresh_cb': refresh_cb,
        })

        fb = Fitbit(**kwargs)
        profile_url = Fitbit.API_ENDPOINT + '/1/user/-/profile.json'
        with requests_mock.mock() as m:
            m.get(profile_url, [{
                'text': json.dumps({
                    "errors": [{
                        "errorType": "expired_token",
                        "message": "Access token expired:"
                    }]
                }),
                'status_code': 401
            }, {
                'text': '{"user":{"aboutMe": "python-fitbit developer"}}',
                'status_code': 200
            }])
            token = {
                'access_token': 'fake_return_access_token',
                'refresh_token': 'fake_return_refresh_token'
            }
            m.post(fb.client.refresh_token_url, text=json.dumps(token))
            retval = fb.make_request(profile_url)

        self.assertEqual(m.request_history[1].path, '/oauth2/token')
        self.assertEqual(
            m.request_history[1].headers['Authorization'],
            _basic_auth_str(
                self.client_kwargs['client_id'],
                self.client_kwargs['client_secret']
            )
        )
        self.assertEqual(retval['user']['aboutMe'], "python-fitbit developer")
        self.assertEqual("fake_return_access_token", token['access_token'])
        self.assertEqual("fake_return_refresh_token", token['refresh_token'])
        refresh_cb.assert_called_once_with(token)

    def test_auto_refresh_error(self):
        """Test of auto_refresh with expired refresh token"""

        refresh_cb = mock.MagicMock()
        kwargs = copy.copy(self.client_kwargs)
        kwargs.update({
            'access_token': 'fake_access_token',
            'refresh_token': 'fake_refresh_token',
            'refresh_cb': refresh_cb,
        })

        fb = Fitbit(**kwargs)
        with requests_mock.mock() as m:
            response = {
                "errors": [{"errorType": "invalid_grant"}],
                "success": False
            }
            m.post(fb.client.refresh_token_url, text=json.dumps(response))
            self.assertRaises(InvalidGrantError, fb.client.refresh_token)


class fake_response(object):
    def __init__(self, code, text):
        self.status_code = code
        self.text = text
        self.content = text
