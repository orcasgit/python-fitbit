import unittest

class APITestCase(unittest.TestCase):


    def __init__(self, consumer_key="", consumer_secret="", client_key=None, client_secret=None, *args, **kwargs):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.client_key = client_key
        self.client_secret = client_secret

        self.client_kwargs = {
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "client_key": client_key,
            "client_secret": client_secret,
        }
        super(APITestCase, self).__init__(*args, **kwargs)
