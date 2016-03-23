import unittest
from .test_exceptions import ExceptionTest
from .test_auth import Auth2Test
from .test_api import (
    APITest,
    CollectionResourceTest,
    DeleteCollectionResourceTest,
    ResourceAccessTest,
    SubscriptionsTest,
    PartnerAPITest
)


def all_tests(consumer_key="", consumer_secret="", user_key=None, user_secret=None):
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExceptionTest))
    suite.addTest(unittest.makeSuite(Auth2Test))
    suite.addTest(unittest.makeSuite(APITest))
    suite.addTest(unittest.makeSuite(CollectionResourceTest))
    suite.addTest(unittest.makeSuite(DeleteCollectionResourceTest))
    suite.addTest(unittest.makeSuite(ResourceAccessTest))
    suite.addTest(unittest.makeSuite(SubscriptionsTest))
    suite.addTest(unittest.makeSuite(PartnerAPITest))
    return suite
