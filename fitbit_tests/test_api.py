from unittest import TestCase
import datetime
import mock
import requests
from fitbit import Fitbit
from fitbit.exceptions import DeleteError, Timeout

URLBASE = "%s/%s/user" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)


class TestBase(TestCase):
    def setUp(self):
        self.fb = Fitbit('x', 'y')

    def common_api_test(self, funcname, args, kwargs, expected_args, expected_kwargs):
        # Create a fitbit object, call the named function on it with the given
        # arguments and verify that make_request is called with the expected args and kwargs
        with mock.patch.object(self.fb, 'make_request') as make_request:
            retval = getattr(self.fb, funcname)(*args, **kwargs)
        mr_args, mr_kwargs = make_request.call_args
        self.assertEqual(expected_args, mr_args)
        self.assertEqual(expected_kwargs, mr_kwargs)

    def verify_raises(self, funcname, args, kwargs, exc):
        self.assertRaises(exc, getattr(self.fb, funcname), *args, **kwargs)


class TimeoutTest(TestCase):

    def setUp(self):
        self.fb = Fitbit('x', 'y')
        self.fb_timeout = Fitbit('x', 'y', timeout=10)

        self.test_url = 'invalid://do.not.connect'

    def test_fb_without_timeout(self):
        with mock.patch.object(self.fb.client.session, 'request') as request:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.content = b'{}'
            request.return_value = mock_response
            result = self.fb.make_request(self.test_url)

        request.assert_called_once()
        self.assertNotIn('timeout', request.call_args[1])
        self.assertEqual({}, result)

    def test_fb_with_timeout__timing_out(self):
        with mock.patch.object(self.fb_timeout.client.session, 'request') as request:
            request.side_effect = requests.Timeout('Timed out')
            with self.assertRaisesRegexp(Timeout, 'Timed out'):
                self.fb_timeout.make_request(self.test_url)

        request.assert_called_once()
        self.assertEqual(10, request.call_args[1]['timeout'])

    def test_fb_with_timeout__not_timing_out(self):
        with mock.patch.object(self.fb_timeout.client.session, 'request') as request:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.content = b'{}'
            request.return_value = mock_response

            result = self.fb_timeout.make_request(self.test_url)

        request.assert_called_once()
        self.assertEqual(10, request.call_args[1]['timeout'])
        self.assertEqual({}, result)


class APITest(TestBase):
    """
    Tests for python-fitbit API, not directly involved in getting
    authenticated
    """

    def test_make_request(self):
        # If make_request returns a response with status 200,
        # we get back the json decoded value that was in the response.content
        ARGS = (1, 2)
        KWARGS = {'a': 3, 'b': 4, 'headers': {'Accept-Language': self.fb.system}}
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.content = b"1"
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
        KWARGS = {'a': 3, 'b': 4, 'Accept-Language': self.fb.system}
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
        KWARGS = {'a': 3, 'b': 4, 'method': 'DELETE', 'Accept-Language': self.fb.system}
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
        KWARGS = {'a': 3, 'b': 4, 'method': 'DELETE', 'Accept-Language': self.fb.system}
        with mock.patch.object(self.fb.client, 'make_request') as client_make_request:
            client_make_request.return_value = mock_response
            self.assertRaises(DeleteError, self.fb.make_request, *ARGS, **KWARGS)


class CollectionResourceTest(TestBase):
    """ Tests for _COLLECTION_RESOURCE """
    def test_all_args(self):
        # If we pass all the optional args, the right things happen
        resource = "RESOURCE"
        date = datetime.date(1962, 1, 13)
        user_id = "bilbo"
        data = {'a': 1, 'b': 2}
        expected_data = data.copy()
        expected_data['date'] = date.strftime("%Y-%m-%d")
        url = URLBASE + "/%s/%s.json" % (user_id, resource)
        self.common_api_test('_COLLECTION_RESOURCE', (resource, date, user_id, data), {}, (url, expected_data), {})

    def test_date_string(self):
        # date can be a "yyyy-mm-dd" string
        resource = "RESOURCE"
        date = "1962-1-13"
        user_id = "bilbo"
        data = {'a': 1, 'b': 2}
        expected_data = data.copy()
        expected_data['date'] = date
        url = URLBASE + "/%s/%s.json" % (user_id, resource)
        self.common_api_test('_COLLECTION_RESOURCE', (resource, date, user_id, data), {}, (url, expected_data), {})

    def test_no_date(self):
        # If we omit the date, it uses today
        resource = "RESOURCE"
        user_id = "bilbo"
        data = {'a': 1, 'b': 2}
        expected_data = data.copy()
        expected_data['date'] = datetime.date.today().strftime("%Y-%m-%d")  # expect today
        url = URLBASE + "/%s/%s.json" % (user_id, resource)
        self.common_api_test('_COLLECTION_RESOURCE', (resource, None, user_id, data), {}, (url, expected_data), {})

    def test_no_userid(self):
        # If we omit the user_id, it uses "-"
        resource = "RESOURCE"
        date = datetime.date(1962, 1, 13)
        user_id = None
        data = {'a': 1, 'b': 2}
        expected_data = data.copy()
        expected_data['date'] = date.strftime("%Y-%m-%d")
        expected_user_id = "-"
        url = URLBASE + "/%s/%s.json" % (expected_user_id, resource)
        self.common_api_test(
            '_COLLECTION_RESOURCE',
            (resource, date, user_id, data), {},
            (url, expected_data),
            {}
        )

    def test_no_data(self):
        # If we omit the data arg, it does the right thing
        resource = "RESOURCE"
        date = datetime.date(1962, 1, 13)
        user_id = "bilbo"
        data = None
        url = URLBASE + "/%s/%s/date/%s.json" % (user_id, resource, date)
        self.common_api_test('_COLLECTION_RESOURCE', (resource, date, user_id, data), {}, (url, data), {})

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
        url = URLBASE + "/-/%s/%s.json" % (resource, log_id)
        self.common_api_test(
            '_DELETE_COLLECTION_RESOURCE',
            (resource, log_id), {},
            (url,),
            {"method": "DELETE"}
        )

    def test_cant_delete_body(self):
        self.assertFalse(hasattr(self.fb, 'delete_body'))

    def test_delete_foods_log(self):
        log_id = "fake_log_id"
        # We need to mock _DELETE_COLLECTION_RESOURCE before we create the Fitbit object,
        # since the __init__ is going to set up references to it
        with mock.patch('fitbit.api.Fitbit._DELETE_COLLECTION_RESOURCE') as delete_resource:
            delete_resource.return_value = 999
            fb = Fitbit('x', 'y')
            retval = fb.delete_foods_log(log_id=log_id)
        args, kwargs = delete_resource.call_args
        self.assertEqual(('foods/log',), args)
        self.assertEqual({'log_id': log_id}, kwargs)
        self.assertEqual(999, retval)

    def test_delete_foods_log_water(self):
        log_id = "OmarKhayyam"
        # We need to mock _DELETE_COLLECTION_RESOURCE before we create the Fitbit object,
        # since the __init__ is going to set up references to it
        with mock.patch('fitbit.api.Fitbit._DELETE_COLLECTION_RESOURCE') as delete_resource:
            delete_resource.return_value = 999
            fb = Fitbit('x', 'y')
            retval = fb.delete_foods_log_water(log_id=log_id)
        args, kwargs = delete_resource.call_args
        self.assertEqual(('foods/log/water',), args)
        self.assertEqual({'log_id': log_id}, kwargs)
        self.assertEqual(999, retval)


class ResourceAccessTest(TestBase):
    """
    Class for testing the Fitbit Resource Access API:
    https://dev.fitbit.com/docs/
    """
    def test_user_profile_get(self):
        """
        Test getting a user profile.
        https://dev.fitbit.com/docs/user/

        Tests the following HTTP method/URLs:
        GET https://api.fitbit.com/1/user/FOO/profile.json
        GET https://api.fitbit.com/1/user/-/profile.json
        """
        user_id = "FOO"
        url = URLBASE + "/%s/profile.json" % user_id
        self.common_api_test('user_profile_get', (user_id,), {}, (url,), {})
        url = URLBASE + "/-/profile.json"
        self.common_api_test('user_profile_get', (), {}, (url,), {})

    def test_user_profile_update(self):
        """
        Test updating a user profile.
        https://dev.fitbit.com/docs/user/#update-profile

        Tests the following HTTP method/URLs:
        POST https://api.fitbit.com/1/user/-/profile.json
        """
        data = "BAR"
        url = URLBASE + "/-/profile.json"
        self.common_api_test('user_profile_update', (data,), {}, (url, data), {})

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

    def test_body_fat_goal(self):
        self.common_api_test(
            'body_fat_goal', (), dict(),
            (URLBASE + '/-/body/log/fat/goal.json',), {'data': {}})
        self.common_api_test(
            'body_fat_goal', (), dict(fat=10),
            (URLBASE + '/-/body/log/fat/goal.json',), {'data': {'fat': 10}})

    def test_body_weight_goal(self):
        self.common_api_test(
            'body_weight_goal', (), dict(),
            (URLBASE + '/-/body/log/weight/goal.json',), {'data': {}})
        self.common_api_test(
            'body_weight_goal', (), dict(start_date='2015-04-01', start_weight=180),
            (URLBASE + '/-/body/log/weight/goal.json',),
            {'data': {'startDate': '2015-04-01', 'startWeight': 180}})
        self.verify_raises('body_weight_goal', (), {'start_date': '2015-04-01'}, ValueError)
        self.verify_raises('body_weight_goal', (), {'start_weight': 180}, ValueError)

    def test_activities_daily_goal(self):
        self.common_api_test(
            'activities_daily_goal', (), dict(),
            (URLBASE + '/-/activities/goals/daily.json',), {'data': {}})
        self.common_api_test(
            'activities_daily_goal', (), dict(steps=10000),
            (URLBASE + '/-/activities/goals/daily.json',), {'data': {'steps': 10000}})
        self.common_api_test(
            'activities_daily_goal', (),
            dict(calories_out=3107, active_minutes=30, floors=10, distance=5, steps=10000),
            (URLBASE + '/-/activities/goals/daily.json',),
            {'data': {'caloriesOut': 3107, 'activeMinutes': 30, 'floors': 10, 'distance': 5, 'steps': 10000}})

    def test_activities_weekly_goal(self):
        self.common_api_test(
            'activities_weekly_goal', (), dict(),
            (URLBASE + '/-/activities/goals/weekly.json',), {'data': {}})
        self.common_api_test(
            'activities_weekly_goal', (), dict(steps=10000),
            (URLBASE + '/-/activities/goals/weekly.json',), {'data': {'steps': 10000}})
        self.common_api_test(
            'activities_weekly_goal', (),
            dict(floors=10, distance=5, steps=10000),
            (URLBASE + '/-/activities/goals/weekly.json',),
            {'data': {'floors': 10, 'distance': 5, 'steps': 10000}})

    def test_food_goal(self):
        self.common_api_test(
            'food_goal', (), dict(),
            (URLBASE + '/-/foods/log/goal.json',), {'data': {}})
        self.common_api_test(
            'food_goal', (), dict(calories=2300),
            (URLBASE + '/-/foods/log/goal.json',), {'data': {'calories': 2300}})
        self.common_api_test(
            'food_goal', (), dict(intensity='EASIER', personalized=True),
            (URLBASE + '/-/foods/log/goal.json',),
            {'data': {'intensity': 'EASIER', 'personalized': True}})
        self.verify_raises('food_goal', (), {'personalized': True}, ValueError)

    def test_water_goal(self):
        self.common_api_test(
            'water_goal', (), dict(),
            (URLBASE + '/-/foods/log/water/goal.json',), {'data': {}})
        self.common_api_test(
            'water_goal', (), dict(target=63),
            (URLBASE + '/-/foods/log/water/goal.json',), {'data': {'target': 63}})

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

    def test_sleep(self):
        today = datetime.date.today().strftime('%Y-%m-%d')
        self.common_api_test('sleep', (today,), {}, ("%s/-/sleep/date/%s.json" % (URLBASE, today), None), {})
        self.common_api_test('sleep', (today, "USER_ID"), {}, ("%s/USER_ID/sleep/date/%s.json" % (URLBASE, today), None), {})

    def test_foods(self):
        today = datetime.date.today().strftime('%Y-%m-%d')
        self.common_api_test('recent_foods', ("USER_ID",), {}, (URLBASE+"/USER_ID/foods/log/recent.json",), {})
        self.common_api_test('favorite_foods', ("USER_ID",), {}, (URLBASE+"/USER_ID/foods/log/favorite.json",), {})
        self.common_api_test('frequent_foods', ("USER_ID",), {}, (URLBASE+"/USER_ID/foods/log/frequent.json",), {})
        self.common_api_test('foods_log', (today, "USER_ID",), {}, ("%s/USER_ID/foods/log/date/%s.json" % (URLBASE, today), None), {})
        self.common_api_test('recent_foods', (), {}, (URLBASE+"/-/foods/log/recent.json",), {})
        self.common_api_test('favorite_foods', (), {}, (URLBASE+"/-/foods/log/favorite.json",), {})
        self.common_api_test('frequent_foods', (), {}, (URLBASE+"/-/foods/log/frequent.json",), {})
        self.common_api_test('foods_log', (today,), {}, ("%s/-/foods/log/date/%s.json" % (URLBASE, today), None), {})

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
        """
        Test the getting/creating/deleting various activity related items.
        Tests the following HTTP method/URLs:

        GET https://api.fitbit.com/1/activities.json
        POST https://api.fitbit.com/1/user/-/activities.json
        GET https://api.fitbit.com/1/activities/FOOBAR.json
        POST https://api.fitbit.com/1/user/-/activities/favorite/activity_id.json
        DELETE https://api.fitbit.com/1/user/-/activities/favorite/activity_id.json
        """
        url = "%s/%s/activities.json" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)
        self.common_api_test('activities_list', (), {}, (url,), {})
        url = "%s/%s/user/-/activities.json" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)
        self.common_api_test('log_activity', (), {'data' : 'FOO'}, (url,), {'data' : 'FOO'} )
        url = "%s/%s/activities/FOOBAR.json" % (Fitbit.API_ENDPOINT, Fitbit.API_VERSION)
        self.common_api_test('activity_detail', ("FOOBAR",), {}, (url,), {})

        url = URLBASE + "/-/activities/favorite/activity_id.json"
        self.common_api_test('add_favorite_activity', ('activity_id',), {}, (url,), {'method': 'POST'})
        self.common_api_test('delete_favorite_activity', ('activity_id',), {}, (url,), {'method': 'DELETE'})

    def _test_get_bodyweight(self, base_date=None, user_id=None, period=None,
                             end_date=None, expected_url=None):
        """ Helper method for testing retrieving body weight measurements """
        with mock.patch.object(self.fb, 'make_request') as make_request:
            self.fb.get_bodyweight(base_date, user_id=user_id, period=period,
                                   end_date=end_date)
        args, kwargs = make_request.call_args
        self.assertEqual((expected_url,), args)

    def test_bodyweight(self):
        """
        Tests for retrieving body weight measurements.
        https://dev.fitbit.com/docs/body/#get-weight-logs
        Tests the following methods/URLs:
        GET https://api.fitbit.com/1/user/-/body/log/weight/date/1992-05-12.json
        GET https://api.fitbit.com/1/user/BAR/body/log/weight/date/1992-05-12/1998-12-31.json
        GET https://api.fitbit.com/1/user/BAR/body/log/weight/date/1992-05-12/1d.json
        GET https://api.fitbit.com/1/user/-/body/log/weight/date/2015-02-26.json
        """
        user_id = 'BAR'

        # No end_date or period
        self._test_get_bodyweight(
            base_date=datetime.date(1992, 5, 12), user_id=None, period=None,
            end_date=None,
            expected_url=URLBASE + "/-/body/log/weight/date/1992-05-12.json")
        # With end_date
        self._test_get_bodyweight(
            base_date=datetime.date(1992, 5, 12), user_id=user_id, period=None,
            end_date=datetime.date(1998, 12, 31),
            expected_url=URLBASE + "/BAR/body/log/weight/date/1992-05-12/1998-12-31.json")
        # With period
        self._test_get_bodyweight(
            base_date=datetime.date(1992, 5, 12), user_id=user_id, period="1d",
            end_date=None,
            expected_url=URLBASE + "/BAR/body/log/weight/date/1992-05-12/1d.json")
        # Date defaults to today
        today = datetime.date.today().strftime('%Y-%m-%d')
        self._test_get_bodyweight(
            base_date=None, user_id=None, period=None, end_date=None,
            expected_url=URLBASE + "/-/body/log/weight/date/%s.json" % today)

    def _test_get_bodyfat(self, base_date=None, user_id=None, period=None,
                          end_date=None, expected_url=None):
        """ Helper method for testing getting bodyfat measurements """
        with mock.patch.object(self.fb, 'make_request') as make_request:
            self.fb.get_bodyfat(base_date, user_id=user_id, period=period,
                                end_date=end_date)
        args, kwargs = make_request.call_args
        self.assertEqual((expected_url,), args)

    def test_bodyfat(self):
        """
        Tests for retrieving bodyfat measurements.
        https://dev.fitbit.com/docs/body/#get-body-fat-logs
        Tests the following methods/URLs:
        GET https://api.fitbit.com/1/user/-/body/log/fat/date/1992-05-12.json
        GET https://api.fitbit.com/1/user/BAR/body/log/fat/date/1992-05-12/1998-12-31.json
        GET https://api.fitbit.com/1/user/BAR/body/log/fat/date/1992-05-12/1d.json
        GET https://api.fitbit.com/1/user/-/body/log/fat/date/2015-02-26.json
        """
        user_id = 'BAR'

        # No end_date or period
        self._test_get_bodyfat(
            base_date=datetime.date(1992, 5, 12), user_id=None, period=None,
            end_date=None,
            expected_url=URLBASE + "/-/body/log/fat/date/1992-05-12.json")
        # With end_date
        self._test_get_bodyfat(
            base_date=datetime.date(1992, 5, 12), user_id=user_id, period=None,
            end_date=datetime.date(1998, 12, 31),
            expected_url=URLBASE + "/BAR/body/log/fat/date/1992-05-12/1998-12-31.json")
        # With period
        self._test_get_bodyfat(
            base_date=datetime.date(1992, 5, 12), user_id=user_id, period="1d",
            end_date=None,
            expected_url=URLBASE + "/BAR/body/log/fat/date/1992-05-12/1d.json")
        # Date defaults to today
        today = datetime.date.today().strftime('%Y-%m-%d')
        self._test_get_bodyfat(
            base_date=None, user_id=None, period=None, end_date=None,
            expected_url=URLBASE + "/-/body/log/fat/date/%s.json" % today)

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


class SubscriptionsTest(TestBase):
    """
    Class for testing the Fitbit Subscriptions API:
    https://dev.fitbit.com/docs/subscriptions/
    """

    def test_subscriptions(self):
        """
        Subscriptions tests. Tests the following methods/URLs:
        GET https://api.fitbit.com/1/user/-/apiSubscriptions.json
        GET https://api.fitbit.com/1/user/-/FOO/apiSubscriptions.json
        POST https://api.fitbit.com/1/user/-/apiSubscriptions/SUBSCRIPTION_ID.json
        POST https://api.fitbit.com/1/user/-/apiSubscriptions/SUBSCRIPTION_ID.json
        POST https://api.fitbit.com/1/user/-/COLLECTION/apiSubscriptions/SUBSCRIPTION_ID-COLLECTION.json
        """
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


class PartnerAPITest(TestBase):
    """
    Class for testing the Fitbit Partner API:
    https://dev.fitbit.com/docs/
    """

    def _test_intraday_timeseries(self, resource, base_date, detail_level,
                                  start_time, end_time, expected_url):
        """ Helper method for intraday timeseries tests """
        with mock.patch.object(self.fb, 'make_request') as make_request:
            retval = self.fb.intraday_time_series(
                resource, base_date, detail_level, start_time, end_time)
        args, kwargs = make_request.call_args
        self.assertEqual((expected_url,), args)

    def test_intraday_timeseries(self):
        """
        Intraday Time Series tests:
        https://dev.fitbit.com/docs/activity/#get-activity-intraday-time-series

        Tests the following methods/URLs:
        GET https://api.fitbit.com/1/user/-/FOO/date/1918-05-11/1d/1min.json
        GET https://api.fitbit.com/1/user/-/FOO/date/1918-05-11/1d/1min.json
        GET https://api.fitbit.com/1/user/-/FOO/date/1918-05-11/1d/1min/time/03:56/15:07.json
        GET https://api.fitbit.com/1/user/-/FOO/date/1918-05-11/1d/1min/time/3:56/15:07.json
        """
        resource = 'FOO'
        base_date = '1918-05-11'

        # detail_level must be valid
        self.assertRaises(
            ValueError,
            self.fb.intraday_time_series,
            resource,
            base_date,
            detail_level="xyz",
            start_time=None,
            end_time=None)

        # provide end_time if start_time provided
        self.assertRaises(
            TypeError,
            self.fb.intraday_time_series,
            resource,
            base_date,
            detail_level="1min",
            start_time='12:55',
            end_time=None)
        self.assertRaises(
            TypeError,
            self.fb.intraday_time_series,
            resource,
            base_date,
            detail_level="1min",
            start_time='12:55',
            end_time='')

        # provide start_time if end_time provided
        self.assertRaises(
            TypeError,
            self.fb.intraday_time_series,
            resource,
            base_date,
            detail_level="1min",
            start_time=None,
            end_time='12:55')
        self.assertRaises(
            TypeError,
            self.fb.intraday_time_series,
            resource,
            base_date,
            detail_level="1min",
            start_time='',
            end_time='12:55')

        # Default
        self._test_intraday_timeseries(
            resource, base_date=base_date, detail_level='1min',
            start_time=None, end_time=None,
            expected_url=URLBASE + "/-/FOO/date/1918-05-11/1d/1min.json")
        # start_date can be a date object
        self._test_intraday_timeseries(
            resource, base_date=datetime.date(1918, 5, 11),
            detail_level='1min', start_time=None, end_time=None,
            expected_url=URLBASE + "/-/FOO/date/1918-05-11/1d/1min.json")
        # start_time can be a datetime object
        self._test_intraday_timeseries(
            resource, base_date=base_date, detail_level='1min',
            start_time=datetime.time(3, 56), end_time='15:07',
            expected_url=URLBASE + "/-/FOO/date/1918-05-11/1d/1min/time/03:56/15:07.json")
        # end_time can be a datetime object
        self._test_intraday_timeseries(
            resource, base_date=base_date, detail_level='1min',
            start_time='3:56', end_time=datetime.time(15, 7),
            expected_url=URLBASE + "/-/FOO/date/1918-05-11/1d/1min/time/3:56/15:07.json")
        # start_time can be a midnight datetime object
        self._test_intraday_timeseries(
            resource, base_date=base_date, detail_level='1min',
            start_time=datetime.time(0, 0), end_time=datetime.time(15, 7),
            expected_url=URLBASE + "/-/FOO/date/1918-05-11/1d/1min/time/00:00/15:07.json")
        # end_time can be a midnight datetime object
        self._test_intraday_timeseries(
            resource, base_date=base_date, detail_level='1min',
            start_time=datetime.time(3, 56), end_time=datetime.time(0, 0),
            expected_url=URLBASE + "/-/FOO/date/1918-05-11/1d/1min/time/03:56/00:00.json")
        # start_time and end_time can be a midnight datetime object
        self._test_intraday_timeseries(
            resource, base_date=base_date, detail_level='1min',
            start_time=datetime.time(0, 0), end_time=datetime.time(0, 0),
            expected_url=URLBASE + "/-/FOO/date/1918-05-11/1d/1min/time/00:00/00:00.json")
