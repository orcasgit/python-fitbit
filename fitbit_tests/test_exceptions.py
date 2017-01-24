import unittest
import json
import mock
import requests
import sys
from fitbit import Fitbit
from fitbit import exceptions


class ExceptionTest(unittest.TestCase):
    """
    Tests that certain response codes raise certain exceptions
    """
    client_kwargs = {
        "client_id": "",
        "client_secret": "",
        "access_token": None,
        "refresh_token": None
    }

    def test_response_ok(self):
        """
        This mocks a pretty normal resource, that the request was authenticated,
        and data was returned.  This test should just run and not raise any
        exceptions
        """
        r = mock.Mock(spec=requests.Response)
        r.status_code = 200
        r.content = b'{"normal": "resource"}'

        f = Fitbit(**self.client_kwargs)
        f.client._request = lambda *args, **kwargs: r
        f.user_profile_get()

        r.status_code = 202
        f.user_profile_get()

        r.status_code = 204
        f.user_profile_get()

    def test_response_auth(self):
        """
        This test checks how the client handles different auth responses, and
        the exceptions raised by the client.
        """
        r = mock.Mock(spec=requests.Response)
        r.status_code = 401
        json_response = {
            "errors": [{
                "errorType": "unauthorized",
                "message": "Unknown auth error"}
            ],
            "normal": "resource"
        }
        r.content = json.dumps(json_response).encode('utf8')

        f = Fitbit(**self.client_kwargs)
        f.client._request = lambda *args, **kwargs: r

        self.assertRaises(exceptions.HTTPUnauthorized, f.user_profile_get)

        r.status_code = 403
        json_response['errors'][0].update({
            "errorType": "forbidden",
            "message": "Forbidden"
        })
        r.content = json.dumps(json_response).encode('utf8')
        self.assertRaises(exceptions.HTTPForbidden, f.user_profile_get)

    def test_response_error(self):
        """
        Tests other HTTP errors
        """
        r = mock.Mock(spec=requests.Response)
        r.content = b'{"normal": "resource"}'

        self.client_kwargs['oauth2'] = True
        f = Fitbit(**self.client_kwargs)
        f.client._request = lambda *args, **kwargs: r

        r.status_code = 404
        self.assertRaises(exceptions.HTTPNotFound, f.user_profile_get)

        r.status_code = 409
        self.assertRaises(exceptions.HTTPConflict, f.user_profile_get)

        r.status_code = 500
        self.assertRaises(exceptions.HTTPServerError, f.user_profile_get)

        r.status_code = 499
        self.assertRaises(exceptions.HTTPBadRequest, f.user_profile_get)

    def test_too_many_requests(self):
        """
        Tests the 429 response, given in case of exceeding the rate limit
        """
        r = mock.Mock(spec=requests.Response)
        r.content = b"{'normal': 'resource'}"
        r.headers = {'Retry-After': '10'}

        f = Fitbit(**self.client_kwargs)
        f.client._request = lambda *args, **kwargs: r

        r.status_code = 429
        try:
            f.user_profile_get()
            self.assertEqual(True, False)  # Won't run if an exception's raised
        except exceptions.HTTPTooManyRequests:
            e = sys.exc_info()[1]
            self.assertEqual(e.retry_after_secs, 10)

    def test_serialization(self):
        """
        Tests non-json data returned
        """
        r = mock.Mock(spec=requests.Response)
        r.status_code = 200
        r.content = b"iyam not jason"

        f = Fitbit(**self.client_kwargs)
        f.client._request = lambda *args, **kwargs: r
        self.assertRaises(exceptions.BadResponse, f.user_profile_get)

    def test_delete_error(self):
        """
        Delete requests should return 204
        """
        r = mock.Mock(spec=requests.Response)
        r.status_code = 201
        r.content = b'{"it\'s all": "ok"}'

        f = Fitbit(**self.client_kwargs)
        f.client._request = lambda *args, **kwargs: r
        self.assertRaises(exceptions.DeleteError, f.delete_activities, 12345)
