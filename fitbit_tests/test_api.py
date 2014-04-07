from unittest import TestCase
import datetime
import mock
from fitbit import Fitbit
from fitbit.exceptions import DeleteError

URLBASE = "%s/%s/user" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)


class TestBase(TestCase):
    def setUp(self):
        self.fb = Fitbit('x', 'y')

    def common_api_test(self, funcname, args, kwargs, expected_args, expected_kwargs):
        # Create a fitbit object, call the named function on it with the given
        # arguments and verify that make_request is called with the expected args and kwargs
        with mock.patch.object(self.fb, 'make_request') as make_request:
            retval = getattr(self.fb, funcname)(*args, **kwargs)
        args, kwargs = make_request.call_args
        self.assertEqual(expected_args, args)
        self.assertEqual(expected_kwargs, kwargs)

    def verify_raises(self, funcname, args, kwargs, exc):
        self.assertRaises(exc, getattr(self.fb, funcname), *args, **kwargs)

class APITest(TestBase):
    """Tests for python-fitbit API, not directly involved in getting authenticated"""

    def test_make_request(self):
        # If make_request returns a response with status 200,
        # we get back the json decoded value that was in the response.content
        ARGS = (1, 2)
        KWARGS = { 'a': 3, 'b': 4, 'headers': {'Accept-Language': self.fb.SYSTEM}}
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.content = "1"
        with mock.patch.object(self.fb.client, 'make_request') as client_make_request:
            client_make_request.return_value = mock_response
            retval = self.fb.make_request(*ARGS, **KWARGS)
        self.assertEqual(1, client_make_request.call_count)
        self.assertEqual(1, retval)
        args, kwargs = client_make_request.call_args
        self.assertEqual(ARGS, args)
        self.assertEqual(KWARGS, kwargs)

    def test_make_request_202(self):
        # If make_request returns a response with status 202,
        # we get back True
        mock_response = mock.Mock()
        mock_response.status_code = 202
        mock_response.content = "1"
        ARGS = (1, 2)
        KWARGS = { 'a': 3, 'b': 4, 'Accept-Language': self.fb.SYSTEM}
        with mock.patch.object(self.fb.client, 'make_request') as client_make_request:
            client_make_request.return_value = mock_response
            retval = self.fb.make_request(*ARGS, **KWARGS)
        self.assertEqual(True, retval)

    def test_make_request_delete_204(self):
        # If make_request returns a response with status 204,
        # and the method is DELETE, we get back True
        mock_response = mock.Mock()
        mock_response.status_code = 204
        mock_response.content = "1"
        ARGS = (1, 2)
        KWARGS = { 'a': 3, 'b': 4, 'method': 'DELETE', 'Accept-Language': self.fb.SYSTEM}
        with mock.patch.object(self.fb.client, 'make_request') as client_make_request:
            client_make_request.return_value = mock_response
            retval = self.fb.make_request(*ARGS, **KWARGS)
        self.assertEqual(True, retval)

    def test_make_request_delete_not_204(self):
        # If make_request returns a response with status not 204,
        # and the method is DELETE, DeleteError is raised
        mock_response = mock.Mock()
        mock_response.status_code = 205
        mock_response.content = "1"
        ARGS = (1, 2)
        KWARGS = { 'a': 3, 'b': 4, 'method': 'DELETE', 'Accept-Language': self.fb.SYSTEM}
        with mock.patch.object(self.fb.client, 'make_request') as client_make_request:
            client_make_request.return_value = mock_response
            self.assertRaises(DeleteError, self.fb.make_request, *ARGS, **KWARGS)

    def test_user_profile_get(self):
        user_id = "FOO"
        url = URLBASE + "/%s/profile.json" % user_id
        self.common_api_test('user_profile_get', (user_id,), {}, (url,), {})

    def test_user_profile_update(self):
        data = "BAR"
        url = URLBASE + "/-/profile.json"
        self.common_api_test('user_profile_update', (data,), {}, (url, data), {})

class CollectionResourceTest(TestBase):
    """Tests for _COLLECTION_RESOURCE"""
    def test_all_args(self):
        # If we pass all the optional args, the right things happen
        resource = "RESOURCE"
        date = datetime.date(1962, 1, 13)
        user_id = "bilbo"
        data = { 'a': 1, 'b': 2}
        expected_data = data.copy()
        expected_data['date'] = date.strftime("%Y-%m-%d")
        url = URLBASE + "/%s/%s.json" % (user_id, resource)
        self.common_api_test('_COLLECTION_RESOURCE', (resource, date, user_id, data), {}, (url, expected_data), {})

    def test_date_string(self):
        # date can be a "yyyy-mm-dd" string
        resource = "RESOURCE"
        date = "1962-1-13"
        user_id = "bilbo"
        data = { 'a': 1, 'b': 2}
        expected_data = data.copy()
        expected_data['date'] = date
        url = URLBASE + "/%s/%s.json" % (user_id, resource)
        self.common_api_test('_COLLECTION_RESOURCE',(resource, date, user_id, data), {}, (url, expected_data), {} )

    def test_no_date(self):
        # If we omit the date, it uses today
        resource = "RESOURCE"
        user_id = "bilbo"
        data = { 'a': 1, 'b': 2}
        expected_data = data.copy()
        expected_data['date'] = datetime.date.today().strftime("%Y-%m-%d")  # expect today
        url = URLBASE + "/%s/%s.json" % (user_id, resource)
        self.common_api_test('_COLLECTION_RESOURCE', (resource, None, user_id, data), {}, (url, expected_data), {})

    def test_no_userid(self):
        # If we omit the user_id, it uses "-"
        resource = "RESOURCE"
        date = datetime.date(1962, 1, 13)
        user_id = None
        data = { 'a': 1, 'b': 2}
        expected_data = data.copy()
        expected_data['date'] = date.strftime("%Y-%m-%d")
        expected_user_id = "-"
        url = URLBASE + "/%s/%s.json" % (expected_user_id, resource)
        self.common_api_test('_COLLECTION_RESOURCE', (resource, date, user_id, data), {}, (url,expected_data), {})

    def test_no_data(self):
        # If we omit the data arg, it does the right thing
        resource = "RESOURCE"
        date = datetime.date(1962, 1, 13)
        user_id = "bilbo"
        data = None
        url = URLBASE + "/%s/%s/date/%s.json" % (user_id, resource, date)
        self.common_api_test('_COLLECTION_RESOURCE', (resource,date,user_id,data), {}, (url,data), {})

    def test_body(self):
        # Test the first method defined in __init__ to see if it calls
        # _COLLECTION_RESOURCE okay - if it does, they should all since
        # they're all built the same way

        # We need to mock _COLLECTION_RESOURCE before we create the Fitbit object,
        # since the __init__ is going to set up references to it
        with mock.patch('fitbit.api.Fitbit._COLLECTION_RESOURCE') as coll_resource:
            coll_resource.return_value = 999
            fb = Fitbit('x', 'y')
            retval = fb.body(date=1, user_id=2, data=3)
        args, kwargs = coll_resource.call_args
        self.assertEqual(('body',), args)
        self.assertEqual({'date': 1, 'user_id': 2, 'data': 3}, kwargs)
        self.assertEqual(999, retval)

class DeleteCollectionResourceTest(TestBase):
    """Tests for _DELETE_COLLECTION_RESOURCE"""
    def test_impl(self):
        # _DELETE_COLLECTION_RESOURCE calls make_request with the right args
        resource = "RESOURCE"
        log_id = "Foo"
        url = URLBASE + "/-/%s/%s.json" % (resource,log_id)
        self.common_api_test('_DELETE_COLLECTION_RESOURCE', (resource, log_id), {},
            (url,), {"method": "DELETE"})

    def test_cant_delete_body(self):
        self.assertFalse(hasattr(self.fb, 'delete_body'))

    def test_delete_water(self):
        log_id = "OmarKhayyam"
        # We need to mock _DELETE_COLLECTION_RESOURCE before we create the Fitbit object,
        # since the __init__ is going to set up references to it
        with mock.patch('fitbit.api.Fitbit._DELETE_COLLECTION_RESOURCE') as delete_resource:
            delete_resource.return_value = 999
            fb = Fitbit('x', 'y')
            retval = fb.delete_water(log_id=log_id)
        args, kwargs = delete_resource.call_args
        self.assertEqual(('water',), args)
        self.assertEqual({'log_id': log_id}, kwargs)
        self.assertEqual(999, retval)

class MiscTest(TestBase):

    def test_recent_activities(self):
        user_id = "LukeSkywalker"
        with mock.patch('fitbit.api.Fitbit.activity_stats') as act_stats:
            fb = Fitbit('x', 'y')
            retval = fb.recent_activities(user_id=user_id)
        args, kwargs = act_stats.call_args
        self.assertEqual((), args)
        self.assertEqual({'user_id': user_id, 'qualifier': 'recent'}, kwargs)

    def test_activity_stats(self):
        user_id = "O B 1 Kenobi"
        qualifier = "frequent"
        url = URLBASE + "/%s/activities/%s.json" % (user_id, qualifier)
        self.common_api_test('activity_stats', (), dict(user_id=user_id, qualifier=qualifier), (url,), {})

    def test_activity_stats_no_qualifier(self):
        user_id = "O B 1 Kenobi"
        qualifier = None
        self.common_api_test('activity_stats', (), dict(user_id=user_id, qualifier=qualifier), (URLBASE + "/%s/activities.json" % user_id,), {})

    def test_timeseries(self):
        resource = 'FOO'
        user_id = 'BAR'
        base_date = '1992-05-12'
        period = '1d'
        end_date = '1998-12-31'

        # Not allowed to specify both period and end date
        self.assertRaises(
            TypeError,
            self.fb.time_series,
            resource,
            user_id,
            base_date,
            period,
            end_date)

        # Period must be valid
        self.assertRaises(
            ValueError,
            self.fb.time_series,
            resource,
            user_id,
            base_date,
            period="xyz",
            end_date=None)

        def test_timeseries(fb, resource, user_id, base_date, period, end_date, expected_url):
            with mock.patch.object(fb, 'make_request') as make_request:
                retval = fb.time_series(resource, user_id, base_date, period, end_date)
            args, kwargs = make_request.call_args
            self.assertEqual((expected_url,), args)

        # User_id defaults = "-"
        test_timeseries(self.fb, resource, user_id=None, base_date=base_date, period=period, end_date=None,
            expected_url=URLBASE + "/-/FOO/date/1992-05-12/1d.json")
        # end_date can be a date object
        test_timeseries(self.fb, resource, user_id=user_id, base_date=base_date, period=None, end_date=datetime.date(1998, 12, 31),
            expected_url=URLBASE + "/BAR/FOO/date/1992-05-12/1998-12-31.json")
        # base_date can be a date object
        test_timeseries(self.fb, resource, user_id=user_id, base_date=datetime.date(1992,5,12), period=None, end_date=end_date,
            expected_url=URLBASE + "/BAR/FOO/date/1992-05-12/1998-12-31.json")

    def test_foods(self):
        self.common_api_test('recent_foods', ("USER_ID",), {}, (URLBASE+"/USER_ID/foods/log/recent.json",), {})
        self.common_api_test('favorite_foods', ("USER_ID",), {}, (URLBASE+"/USER_ID/foods/log/favorite.json",), {})
        self.common_api_test('frequent_foods', ("USER_ID",), {}, (URLBASE+"/USER_ID/foods/log/frequent.json",), {})
        self.common_api_test('recent_foods', (), {}, (URLBASE+"/-/foods/log/recent.json",), {})
        self.common_api_test('favorite_foods', (), {}, (URLBASE+"/-/foods/log/favorite.json",), {})
        self.common_api_test('frequent_foods', (), {}, (URLBASE+"/-/foods/log/frequent.json",), {})

        url = URLBASE + "/-/foods/log/favorite/food_id.json"
        self.common_api_test('add_favorite_food', ('food_id',), {}, (url,), {'method': 'POST'})
        self.common_api_test('delete_favorite_food', ('food_id',), {}, (url,), {'method': 'DELETE'})

        url = URLBASE + "/-/foods.json"
        self.common_api_test('create_food', (), {'data': 'FOO'}, (url,), {'data': 'FOO'})
        url = URLBASE + "/-/meals.json"
        self.common_api_test('get_meals', (), {}, (url,), {})
        url = "%s/%s/foods/search.json?query=FOOBAR" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)
        self.common_api_test('search_foods', ("FOOBAR",), {}, (url,), {})
        url = "%s/%s/foods/FOOBAR.json" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)
        self.common_api_test('food_detail', ("FOOBAR",), {}, (url,), {})
        url = "%s/%s/foods/units.json" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)
        self.common_api_test('food_units', (), {}, (url,), {})

    def test_devices(self):
        url = URLBASE + "/-/devices.json"
        self.common_api_test('get_devices', (), {}, (url,), {})

    def test_badges(self):
        url = URLBASE + "/-/badges.json"
        self.common_api_test('get_badges', (), {}, (url,), {})

    def test_activities(self):
        url = "%s/%s/activities.json" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)
        self.common_api_test('activities_list', (), {}, (url,), {})
        url = "%s/%s/user/-/activities.json" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)
        self.common_api_test('log_activity', (), {'data' : 'FOO'}, (url,), {'data' : 'FOO'} )
        url = "%s/%s/activities/FOOBAR.json" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)
        self.common_api_test('activity_detail', ("FOOBAR",), {}, (url,), {})

    def test_bodyweight(self):
        def test_get_bodyweight(fb, base_date=None, user_id=None, period=None, end_date=None, expected_url=None):
            with mock.patch.object(fb, 'make_request') as make_request:
                fb.get_bodyweight(base_date, user_id=user_id, period=period, end_date=end_date)
            args, kwargs = make_request.call_args
            self.assertEqual((expected_url,), args)

        user_id = 'BAR'

        # No end_date or period
        test_get_bodyweight(self.fb, base_date=datetime.date(1992, 5, 12), user_id=None, period=None, end_date=None,
            expected_url=URLBASE + "/-/body/log/weight/date/1992-05-12.json")
        # With end_date
        test_get_bodyweight(self.fb, base_date=datetime.date(1992, 5, 12), user_id=user_id, period=None, end_date=datetime.date(1998, 12, 31),
            expected_url=URLBASE + "/BAR/body/log/weight/date/1992-05-12/1998-12-31.json")
        # With period
        test_get_bodyweight(self.fb, base_date=datetime.date(1992, 5, 12), user_id=user_id, period="1d", end_date=None,
            expected_url=URLBASE + "/BAR/body/log/weight/date/1992-05-12/1d.json")
        # Date defaults to today
        test_get_bodyweight(self.fb, base_date=None, user_id=None, period=None, end_date=None,
            expected_url=URLBASE + "/-/body/log/weight/date/%s.json" % datetime.date.today().strftime('%Y-%m-%d'))

    def test_bodyfat(self):
        def test_get_bodyfat(fb, base_date=None, user_id=None, period=None, end_date=None, expected_url=None):
            with mock.patch.object(fb, 'make_request') as make_request:
                fb.get_bodyfat(base_date, user_id=user_id, period=period, end_date=end_date)
            args, kwargs = make_request.call_args
            self.assertEqual((expected_url,), args)

        user_id = 'BAR'

        # No end_date or period
        test_get_bodyfat(self.fb, base_date=datetime.date(1992, 5, 12), user_id=None, period=None, end_date=None,
            expected_url=URLBASE + "/-/body/log/fat/date/1992-05-12.json")
        # With end_date
        test_get_bodyfat(self.fb, base_date=datetime.date(1992, 5, 12), user_id=user_id, period=None, end_date=datetime.date(1998, 12, 31),
            expected_url=URLBASE + "/BAR/body/log/fat/date/1992-05-12/1998-12-31.json")
        # With period
        test_get_bodyfat(self.fb, base_date=datetime.date(1992, 5, 12), user_id=user_id, period="1d", end_date=None,
            expected_url=URLBASE + "/BAR/body/log/fat/date/1992-05-12/1d.json")
        # Date defaults to today
        test_get_bodyfat(self.fb, base_date=None, user_id=None, period=None, end_date=None,
            expected_url=URLBASE + "/-/body/log/fat/date/%s.json" % datetime.date.today().strftime('%Y-%m-%d'))

    def test_friends(self):
        url = URLBASE + "/-/friends.json"
        self.common_api_test('get_friends', (), {}, (url,), {})
        url = URLBASE + "/FOOBAR/friends.json"
        self.common_api_test('get_friends', ("FOOBAR",), {}, (url,), {})
        url = URLBASE + "/-/friends/leaders/7d.json"
        self.common_api_test('get_friends_leaderboard', ("7d",), {}, (url,), {})
        url = URLBASE + "/-/friends/leaders/30d.json"
        self.common_api_test('get_friends_leaderboard', ("30d",), {}, (url,), {})
        self.verify_raises('get_friends_leaderboard', ("xd",), {}, ValueError)

    def test_invitations(self):
        url = URLBASE + "/-/friends/invitations.json"
        self.common_api_test('invite_friend', ("FOO",), {}, (url,), {'data': "FOO"})
        self.common_api_test('invite_friend_by_email', ("foo@bar",), {}, (url,), {'data':{'invitedUserEmail': "foo@bar"}})
        self.common_api_test('invite_friend_by_userid', ("foo@bar",), {}, (url,), {'data':{'invitedUserId': "foo@bar"}})
        url = URLBASE + "/-/friends/invitations/FOO.json"
        self.common_api_test('respond_to_invite', ("FOO", True), {}, (url,), {'data':{'accept': "true"}})
        self.common_api_test('respond_to_invite', ("FOO", False), {}, (url,), {'data':{'accept': "false"}})
        self.common_api_test('respond_to_invite', ("FOO", ), {}, (url,), {'data':{'accept': "true"}})
        self.common_api_test('accept_invite', ("FOO",), {}, (url,), {'data':{'accept': "true"}})
        self.common_api_test('reject_invite', ("FOO", ), {}, (url,), {'data':{'accept': "false"}})

    def test_subscriptions(self):
        url = URLBASE + "/-/apiSubscriptions.json"
        self.common_api_test('list_subscriptions', (), {}, (url,), {})
        url = URLBASE + "/-/FOO/apiSubscriptions.json"
        self.common_api_test('list_subscriptions', ("FOO",), {}, (url,), {})
        url = URLBASE + "/-/apiSubscriptions/SUBSCRIPTION_ID.json"
        self.common_api_test('subscription', ("SUBSCRIPTION_ID", "SUBSCRIBER_ID"), {},
                (url,), {'method': 'POST', 'headers': {'X-Fitbit-Subscriber-id': "SUBSCRIBER_ID"}})
        self.common_api_test('subscription', ("SUBSCRIPTION_ID", "SUBSCRIBER_ID"), {'method': 'THROW'},
            (url,), {'method': 'THROW', 'headers': {'X-Fitbit-Subscriber-id': "SUBSCRIBER_ID"}})
        url = URLBASE + "/-/COLLECTION/apiSubscriptions/SUBSCRIPTION_ID-COLLECTION.json"
        self.common_api_test('subscription', ("SUBSCRIPTION_ID", "SUBSCRIBER_ID"), {'method': 'THROW', 'collection': "COLLECTION"},
            (url,), {'method': 'THROW', 'headers': {'X-Fitbit-Subscriber-id': "SUBSCRIBER_ID"}})

    def test_alarms(self):
        url = "%s/-/devices/tracker/%s/alarms.json" % (URLBASE, 'FOO')
        self.common_api_test('get_alarms', (), {'device_id': 'FOO'}, (url,), {})
        url = "%s/-/devices/tracker/%s/alarms/%s.json" % (URLBASE, 'FOO', 'BAR')
        self.common_api_test('delete_alarm', (), {'device_id': 'FOO', 'alarm_id': 'BAR'}, (url,), {'method': 'DELETE'})
        url = "%s/-/devices/tracker/%s/alarms.json" % (URLBASE, 'FOO')
        self.common_api_test('add_alarm',
            (),
            {'device_id': 'FOO',
             'alarm_time': datetime.datetime(year=2013, month=11, day=13, hour=8, minute=16),
             'week_days': ['MONDAY']
            },
            (url,),
            {'data':
                 {'enabled': True,
                    'recurring': False,
                    'time': datetime.datetime(year=2013, month=11, day=13, hour=8, minute=16).strftime("%H:%M%z"),
                    'vibe': 'DEFAULT',
                    'weekDays': ['MONDAY'],
                },
            'method': 'POST'
            }
        )
        self.common_api_test('add_alarm',
            (),
            {'device_id': 'FOO',
             'alarm_time': datetime.datetime(year=2013, month=11, day=13, hour=8, minute=16),
             'week_days': ['MONDAY'], 'recurring': True, 'enabled': False, 'label': 'ugh',
             'snooze_length': 5,
             'snooze_count': 5
            },
            (url,),
            {'data':
                 {'enabled': False,
                  'recurring': True,
                  'label': 'ugh',
                  'snoozeLength': 5,
                  'snoozeCount': 5,
                  'time': datetime.datetime(year=2013, month=11, day=13, hour=8, minute=16).strftime("%H:%M%z"),
                  'vibe': 'DEFAULT',
                  'weekDays': ['MONDAY'],
                },
            'method': 'POST'}
        )
        url = "%s/-/devices/tracker/%s/alarms/%s.json" % (URLBASE, 'FOO', 'BAR')
        self.common_api_test('update_alarm',
            (),
            {'device_id': 'FOO',
             'alarm_id': 'BAR',
             'alarm_time': datetime.datetime(year=2013, month=11, day=13, hour=8, minute=16),
             'week_days': ['MONDAY'], 'recurring': True, 'enabled': False, 'label': 'ugh',
             'snooze_length': 5,
             'snooze_count': 5
            },
            (url,),
            {'data':
                 {'enabled': False,
                  'recurring': True,
                  'label': 'ugh',
                  'snoozeLength': 5,
                  'snoozeCount': 5,
                  'time': datetime.datetime(year=2013, month=11, day=13, hour=8, minute=16).strftime("%H:%M%z"),
                  'vibe': 'DEFAULT',
                  'weekDays': ['MONDAY'],
                },
            'method': 'POST'}
        )
