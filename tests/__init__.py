import unittest
from test_exceptions import ExceptionTest
from test_auth import AuthTest


def all_tests(consumer_key="", consumer_secret="", user_key=None, user_secret=None):
    kwargs = {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "user_key": user_key,
        "user_secret": user_secret,
    }
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExceptionTest))
    suite.addTest(unittest.makeSuite(AuthTest))
    return suite
