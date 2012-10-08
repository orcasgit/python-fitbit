from unittest import TestCase
from fitbit import Fitbit
import mock
import oauth2 as oauth

class AuthTest(TestCase):
    """Add tests for auth part of API
    mock the oauth library calls to simulate various responses,
    make sure we call the right oauth calls, respond correctly based on the responses
    """
    client_kwargs = {
        "consumer_key": "",
        "consumer_secret": "",
        "user_key": None,
        "user_secret": None,
        }

    def test_fetch_request_token(self):
        # fetch_request_token needs to make a request and then build a token from the response

        fb = Fitbit(**self.client_kwargs)
        callback_url = "CALLBACK_URL"
        parameters = {'oauth_callback': callback_url}
        with mock.patch.object(oauth.Request, 'from_consumer_and_token') as from_consumer_and_token:
            mock_request = mock.Mock()
            mock_request.to_header.return_value = "MOCKHEADERS"
            mock_request.method = 'GET'
            from_consumer_and_token.return_value = mock_request
            with mock.patch('fitbit.api.FitbitOauthClient._request') as _request:
                fake_response = mock.Mock()
                fake_response.content = "FAKECONTENT"
                fake_response.status_code = 200
                _request.return_value = fake_response
                with mock.patch.object(oauth.Token, 'from_string') as from_string:
                    from_string.return_value = "FAKERETURNVALUE"

                    retval = fb.client.fetch_request_token(parameters)
        # Got the right return value
        self.assertEqual("FAKERETURNVALUE", retval)
        # The right parms were passed along the way to getting there
        self.assertEqual(1, from_consumer_and_token.call_count)
        self.assertEqual((fb.client._consumer,), from_consumer_and_token.call_args[0])
        self.assertEqual({'http_url': fb.client.request_token_url, 'parameters': parameters}, from_consumer_and_token.call_args[1])
        self.assertEqual(1, mock_request.sign_request.call_count)
        self.assertEqual((fb.client._signature_method, fb.client._consumer, None), mock_request.sign_request.call_args[0])
        self.assertEqual(1, _request.call_count)
        self.assertEqual((mock_request.method,fb.client.request_token_url), _request.call_args[0])
        self.assertEqual({'headers': "MOCKHEADERS"}, _request.call_args[1])
        self.assertEqual(1, from_string.call_count)
        self.assertEqual(("FAKECONTENT",), from_string.call_args[0])

    def test_authorize_token_url(self):
        # authorize_token_url calls oauth and returns a URL
        fb = Fitbit(**self.client_kwargs)
        fake_token = "FAKETOKEN"
        with mock.patch.object(oauth.Request, "from_token_and_callback") as from_token_and_callback:
            mock_request = mock.Mock()
            mock_request.to_url.return_value = "FAKEURL"
            from_token_and_callback.return_value = mock_request
            retval = fb.client.authorize_token_url(fake_token)
        self.assertEqual("FAKEURL", retval)
        self.assertEqual(1, from_token_and_callback.call_count)
        kwargs = from_token_and_callback.call_args_list[0][1]
        self.assertEqual({'token': fake_token, 'http_url': fb.client.authorization_url}, kwargs)

    def test_fetch_access_token(self):
        fb = Fitbit(**self.client_kwargs)
        fake_token = "FAKETOKEN"
        fake_verifier = "FAKEVERIFIER"
        with mock.patch.object(oauth.Request, 'from_consumer_and_token') as from_consumer_and_token:
            mock_request = mock.Mock()
            mock_request.to_header.return_value = "FAKEHEADERS"
            from_consumer_and_token.return_value = mock_request
            with mock.patch('fitbit.api.FitbitOauthClient._request') as _request:
                fake_response = mock.Mock()
                fake_response.content = "FAKECONTENT"
                fake_response.status_code = 200
                _request.return_value = fake_response
                with mock.patch.object(oauth.Token, 'from_string') as from_string:
                    from_string.return_value = "FAKERETURNVALUE"
                    with mock.patch('fitbit.api.urlparse') as urlparse:
                        urlparse.parse_qs.return_value = {'encoded_user_id':['foo']}
                        retval = fb.client.fetch_access_token(fake_token, fake_verifier)
        self.assertEqual("FAKERETURNVALUE", retval)
        self.assertEqual('foo', fb.client.user_id)
        expected_args = (fb.client._consumer, fake_token)
        expected_kwargs = {'http_url': fb.client.access_token_url,
                           'http_method': 'POST',
                           'parameters':{'oauth_verifier': fake_verifier}}
        self.assertEqual(expected_args, from_consumer_and_token.call_args[0])
        self.assertEqual(expected_kwargs, from_consumer_and_token.call_args[1])
        expected_args = ('POST', fb.client.access_token_url)
        expected_kwargs = {'data': "oauth_verifier=%s" % fake_verifier,
                           'headers': "FAKEHEADERS"}
        self.assertEqual(expected_args, _request.call_args[0])
        self.assertEqual(expected_kwargs, _request.call_args[1])
        expected_args = ("FAKECONTENT",)
        expected_kwargs = {}
        self.assertEqual(expected_args, from_string.call_args[0])
        self.assertEqual(expected_kwargs, from_string.call_args[1])

    def test_fetch_access_token_error(self):
        fb = Fitbit(**self.client_kwargs)
        fake_token = "FAKETOKEN"
        fake_verifier = "FAKEVERIFIER"
        with mock.patch.object(oauth.Request, 'from_consumer_and_token') as from_consumer_and_token:
            mock_request = mock.Mock()
            mock_request.to_header.return_value = "FAKEHEADERS"
            from_consumer_and_token.return_value = mock_request
            with mock.patch('fitbit.api.FitbitOauthClient._request') as _request:
                fake_response = mock.Mock()
                fake_response.content = "FAKECONTENT"
                fake_response.status_code = 999
                _request.return_value = fake_response
                with mock.patch.object(oauth.Token, 'from_string') as from_string:
                    from_string.return_value = "FAKERETURNVALUE"
                    with mock.patch('fitbit.api.urlparse') as urlparse:
                        urlparse.parse_qs.return_value = {'encoded_user_id':['foo']}
                        self.assertRaises(Exception,
                            fb.client.fetch_access_token,
                            fake_token, fake_verifier)
