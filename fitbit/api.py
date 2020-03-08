# -*- coding: utf-8 -*-
import datetime
import json
import requests

try:
    from urllib.parse import urlencode
except ImportError:
    # Python 2.x
    from urllib import urlencode

from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from . import exceptions
from .compliance import fitbit_compliance_fix
from .utils import curry


class FitbitOauth2Client(object):
    API_ENDPOINT = "https://api.fitbit.com"
    AUTHORIZE_ENDPOINT = "https://www.fitbit.com"
    API_VERSION = 1

    request_token_url = "%s/oauth2/token" % API_ENDPOINT
    authorization_url = "%s/oauth2/authorize" % AUTHORIZE_ENDPOINT
    access_token_url = request_token_url
    refresh_token_url = request_token_url

    def __init__(self, client_id, client_secret, access_token=None,
            refresh_token=None, expires_at=None, refresh_cb=None,
            redirect_uri=None, *args, **kwargs):
        """
        Create a FitbitOauth2Client object. Specify the first 7 parameters if
        you have them to access user data. Specify just the first 2 parameters
        to start the setup for user authorization (as an example see gather_key_oauth2.py)
            - client_id, client_secret are in the app configuration page
            https://dev.fitbit.com/apps
            - access_token, refresh_token are obtained after the user grants permission
        """

        self.client_id, self.client_secret = client_id, client_secret
        token = {}
        if access_token and refresh_token:
            token.update({
                'access_token': access_token,
                'refresh_token': refresh_token
            })
        if expires_at:
            token['expires_at'] = expires_at
        self.session = fitbit_compliance_fix(OAuth2Session(
            client_id,
            auto_refresh_url=self.refresh_token_url,
            token_updater=refresh_cb,
            token=token,
            redirect_uri=redirect_uri,
        ))
        self.timeout = kwargs.get("timeout", None)

    def _request(self, method, url, **kwargs):
        """
        A simple wrapper around requests.
        """
        if self.timeout is not None and 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        try:
            response = self.session.request(method, url, **kwargs)

            # If our current token has no expires_at, or something manages to slip
            # through that check
            if response.status_code == 401:
                d = json.loads(response.content.decode('utf8'))
                if d['errors'][0]['errorType'] == 'expired_token':
                    self.refresh_token()
                    response = self.session.request(method, url, **kwargs)

            return response
        except requests.Timeout as e:
            raise exceptions.Timeout(*e.args)

    def make_request(self, url, data=None, method=None, **kwargs):
        """
        Builds and makes the OAuth2 Request, catches errors

        https://dev.fitbit.com/docs/oauth2/#authorization-errors
        """
        data = data or {}
        method = method or ('POST' if data else 'GET')
        response = self._request(
            method,
            url,
            data=data,
            client_id=self.client_id,
            client_secret=self.client_secret,
            **kwargs
        )

        exceptions.detect_and_raise_error(response)

        return response

    def authorize_token_url(self, scope=None, redirect_uri=None, **kwargs):
        """Step 1: Return the URL the user needs to go to in order to grant us
        authorization to look at their data.  Then redirect the user to that
        URL, open their browser to it, or tell them to copy the URL into their
        browser.
            - scope: pemissions that that are being requested [default ask all]
            - redirect_uri: url to which the response will posted. required here
              unless you specify only one Callback URL on the fitbit app or
              you already passed it to the constructor
            for more info see https://dev.fitbit.com/docs/oauth2/
        """

        self.session.scope = scope or [
            "activity",
            "nutrition",
            "heartrate",
            "location",
            "nutrition",
            "profile",
            "settings",
            "sleep",
            "social",
            "weight",
        ]

        if redirect_uri:
            self.session.redirect_uri = redirect_uri

        return self.session.authorization_url(self.authorization_url, **kwargs)

    def fetch_access_token(self, code, redirect_uri=None):

        """Step 2: Given the code from fitbit from step 1, call
        fitbit again and returns an access token object. Extract the needed
        information from that and save it to use in future API calls.
        the token is internally saved
        """
        if redirect_uri:
            self.session.redirect_uri = redirect_uri
        return self.session.fetch_token(
            self.access_token_url,
            username=self.client_id,
            password=self.client_secret,
            client_secret=self.client_secret,
            code=code)

    def refresh_token(self):
        """Step 3: obtains a new access_token from the the refresh token
        obtained in step 2. Only do the refresh if there is `token_updater(),`
        which saves the token.
        """
        token = {}
        if self.session.token_updater:
            token = self.session.refresh_token(
                self.refresh_token_url,
                auth=HTTPBasicAuth(self.client_id, self.client_secret)
            )
            self.session.token_updater(token)

        return token


class Fitbit(object):
    """
    Before using this class, create a Fitbit app
    `here <https://dev.fitbit.com/apps/new>`_. There you will get the client id
    and secret needed to instantiate this class. When first authorizing a user,
    make sure to pass the `redirect_uri` keyword arg so fitbit will know where
    to return to when the authorization is complete. See
    `gather_keys_oauth2.py <https://github.com/orcasgit/python-fitbit/blob/master/gather_keys_oauth2.py>`_
    for a reference implementation of the authorization process. You should
    save ``access_token``, ``refresh_token``, and ``expires_at`` from the
    returned token for each user you authorize.

    When instantiating this class for use with an already authorized user, pass
    in the ``access_token``, ``refresh_token``, and ``expires_at`` keyword
    arguments. We also strongly recommend passing in a ``refresh_cb`` keyword
    argument, which should be a function taking one argument: a token dict.
    When that argument is present, we will automatically refresh the access
    token when needed and call this function so that you can save the updated
    token data. If you don't save the updated information, then you could end
    up with invalid access and refresh tokens, and the only way to recover from
    that is to reauthorize the user.
    """
    US = 'en_US'
    METRIC = 'en_UK'

    API_ENDPOINT = "https://api.fitbit.com"
    API_VERSION = 1
    WEEK_DAYS = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    PERIODS = ['1d', '7d', '30d', '1w', '1m', '3m', '6m', '1y', 'max']

    RESOURCE_LIST = [
        'body',
        'activities',
        'foods/log',
        'foods/log/water',
        'sleep',
        'heart',
        'bp',
        'glucose',
    ]

    QUALIFIERS = [
        'recent',
        'favorite',
        'frequent',
    ]

    def __init__(self, client_id, client_secret, access_token=None,
            refresh_token=None, expires_at=None, refresh_cb=None,
            redirect_uri=None, system=US, **kwargs):
        """
        Fitbit(<id>, <secret>, access_token=<token>, refresh_token=<token>)
        """
        self.system = system
        self.client = FitbitOauth2Client(
            client_id,
            client_secret,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            refresh_cb=refresh_cb,
            redirect_uri=redirect_uri,
            **kwargs
        )

        # All of these use the same patterns, define the method for accessing
        # creating and deleting records once, and use curry to make individual
        # Methods for each
        for resource in Fitbit.RESOURCE_LIST:
            underscore_resource = resource.replace('/', '_')
            setattr(self, underscore_resource,
                    curry(self._COLLECTION_RESOURCE, resource))

            if resource not in ['body', 'glucose']:
                # Body and Glucose entries are not currently able to be deleted
                setattr(self, 'delete_%s' % underscore_resource, curry(
                    self._DELETE_COLLECTION_RESOURCE, resource))

        for qualifier in Fitbit.QUALIFIERS:
            setattr(self, '%s_activities' % qualifier, curry(self.activity_stats, qualifier=qualifier))
            setattr(self, '%s_foods' % qualifier, curry(self._food_stats,
                                                        qualifier=qualifier))

    def make_request(self, *args, **kwargs):
        # This should handle data level errors, improper requests, and bad
        # serialization
        headers = kwargs.get('headers', {})
        headers.update({'Accept-Language': self.system})
        kwargs['headers'] = headers

        method = kwargs.get('method', 'POST' if 'data' in kwargs else 'GET')
        response = self.client.make_request(*args, **kwargs)

        if response.status_code == 202:
            return True
        if method == 'DELETE':
            if response.status_code == 204:
                return True
            else:
                raise exceptions.DeleteError(response)
        try:
            rep = json.loads(response.content.decode('utf8'))
        except ValueError:
            raise exceptions.BadResponse

        return rep

    def user_profile_get(self, user_id=None):
        """
        Get a user profile. You can get other user's profile information
        by passing user_id, or you can get the current user's by not passing
        a user_id

        .. note:
            This is not the same format that the GET comes back in, GET requests
            are wrapped in {'user': <dict of user data>}

        https://dev.fitbit.com/docs/user/
        """
        url = "{0}/{1}/user/{2}/profile.json".format(*self._get_common_args(user_id))
        return self.make_request(url)

    def user_profile_update(self, data):
        """
        Set a user profile. You can set your user profile information by
        passing a dictionary of attributes that will be updated.

        .. note:
            This is not the same format that the GET comes back in, GET requests
            are wrapped in {'user': <dict of user data>}

        https://dev.fitbit.com/docs/user/#update-profile
        """
        url = "{0}/{1}/user/-/profile.json".format(*self._get_common_args())
        return self.make_request(url, data)

    def _get_common_args(self, user_id=None):
        common_args = (self.API_ENDPOINT, self.API_VERSION,)
        if not user_id:
            user_id = '-'
        common_args += (user_id,)
        return common_args

    def _get_date_string(self, date):
        if not isinstance(date, str):
            return date.strftime('%Y-%m-%d')
        return date

    def _COLLECTION_RESOURCE(self, resource, date=None, user_id=None,
                             data=None):
        """
        Retrieving and logging of each type of collection data.

        Arguments:
            resource, defined automatically via curry
            [date] defaults to today
            [user_id] defaults to current logged in user
            [data] optional, include for creating a record, exclude for access

        This implements the following methods::

            body(date=None, user_id=None, data=None)
            activities(date=None, user_id=None, data=None)
            foods_log(date=None, user_id=None, data=None)
            foods_log_water(date=None, user_id=None, data=None)
            sleep(date=None, user_id=None, data=None)
            heart(date=None, user_id=None, data=None)
            bp(date=None, user_id=None, data=None)

        * https://dev.fitbit.com/docs/
        """

        if not date:
            date = datetime.date.today()
        date_string = self._get_date_string(date)

        kwargs = {'resource': resource, 'date': date_string}
        if not data:
            base_url = "{0}/{1}/user/{2}/{resource}/date/{date}.json"
        else:
            data['date'] = date_string
            base_url = "{0}/{1}/user/{2}/{resource}.json"
        url = base_url.format(*self._get_common_args(user_id), **kwargs)
        return self.make_request(url, data)

    def _DELETE_COLLECTION_RESOURCE(self, resource, log_id):
        """
        deleting each type of collection data

        Arguments:
            resource, defined automatically via curry
            log_id, required, log entry to delete

        This builds the following methods::

            delete_body(log_id)
            delete_activities(log_id)
            delete_foods_log(log_id)
            delete_foods_log_water(log_id)
            delete_sleep(log_id)
            delete_heart(log_id)
            delete_bp(log_id)

        """
        url = "{0}/{1}/user/-/{resource}/{log_id}.json".format(
            *self._get_common_args(),
            resource=resource,
            log_id=log_id
        )
        response = self.make_request(url, method='DELETE')
        return response

    def _resource_goal(self, resource, data={}, period=None):
        """ Handles GETting and POSTing resource goals of all types """
        url = "{0}/{1}/user/-/{resource}/goal{postfix}.json".format(
            *self._get_common_args(),
            resource=resource,
            postfix=('s/' + period) if period else ''
        )
        return self.make_request(url, data=data)

    def _filter_nones(self, data):
        filter_nones = lambda item: item[1] is not None
        filtered_kwargs = list(filter(filter_nones, data.items()))
        return {} if not filtered_kwargs else dict(filtered_kwargs)

    def body_fat_goal(self, fat=None):
        """
        Implements the following APIs

        * https://dev.fitbit.com/docs/body/#get-body-goals
        * https://dev.fitbit.com/docs/body/#update-body-fat-goal

        Pass no arguments to get the body fat goal. Pass a ``fat`` argument
        to update the body fat goal.

        Arguments:
        * ``fat`` -- Target body fat in %; in the format X.XX
        """
        return self._resource_goal('body/log/fat', {'fat': fat} if fat else {})

    def body_weight_goal(self, start_date=None, start_weight=None, weight=None):
        """
        Implements the following APIs

        * https://dev.fitbit.com/docs/body/#get-body-goals
        * https://dev.fitbit.com/docs/body/#update-weight-goal

        Pass no arguments to get the body weight goal. Pass ``start_date``,
        ``start_weight`` and optionally ``weight`` to set the weight goal.
        ``weight`` is required if it hasn't been set yet.

        Arguments:
        * ``start_date`` -- Weight goal start date; in the format yyyy-MM-dd
        * ``start_weight`` -- Weight goal start weight; in the format X.XX
        * ``weight`` -- Weight goal target weight; in the format X.XX
        """
        data = self._filter_nones({
            'startDate': start_date,
            'startWeight': start_weight,
            'weight': weight
        })
        if data and not ('startDate' in data and 'startWeight' in data):
            raise ValueError('start_date and start_weight are both required')
        return self._resource_goal('body/log/weight', data)

    def activities_daily_goal(self, calories_out=None, active_minutes=None,
                              floors=None, distance=None, steps=None):
        """
        Implements the following APIs for period equal to daily

        https://dev.fitbit.com/docs/activity/#get-activity-goals
        https://dev.fitbit.com/docs/activity/#update-activity-goals

        Pass no arguments to get the daily activities goal. Pass any one of
        the optional arguments to set that component of the daily activities
        goal.

        Arguments:
        * ``calories_out`` -- New goal value; in an integer format
        * ``active_minutes`` -- New goal value; in an integer format
        * ``floors`` -- New goal value; in an integer format
        * ``distance`` -- New goal value; in the format X.XX or integer
        * ``steps`` -- New goal value; in an integer format
        """
        data = self._filter_nones({
            'caloriesOut': calories_out,
            'activeMinutes': active_minutes,
            'floors': floors,
            'distance': distance,
            'steps': steps
        })
        return self._resource_goal('activities', data, period='daily')

    def activities_weekly_goal(self, distance=None, floors=None, steps=None):
        """
        Implements the following APIs for period equal to weekly

        https://dev.fitbit.com/docs/activity/#get-activity-goals
        https://dev.fitbit.com/docs/activity/#update-activity-goals

        Pass no arguments to get the weekly activities goal. Pass any one of
        the optional arguments to set that component of the weekly activities
        goal.

        Arguments:
        * ``distance`` -- New goal value; in the format X.XX or integer
        * ``floors`` -- New goal value; in an integer format
        * ``steps`` -- New goal value; in an integer format
        """
        data = self._filter_nones({'distance': distance, 'floors': floors,
                                   'steps': steps})
        return self._resource_goal('activities', data, period='weekly')

    def food_goal(self, calories=None, intensity=None, personalized=None):
        """
        Implements the following APIs

        https://dev.fitbit.com/docs/food-logging/#get-food-goals
        https://dev.fitbit.com/docs/food-logging/#update-food-goal

        Pass no arguments to get the food goal. Pass at least ``calories`` or
        ``intensity`` and optionally ``personalized`` to update the food goal.

        Arguments:
        * ``calories`` -- Manual Calorie Consumption Goal; calories, integer;
        * ``intensity`` -- Food Plan intensity; (MAINTENANCE, EASIER, MEDIUM, KINDAHARD, HARDER);
        * ``personalized`` -- Food Plan type; ``True`` or ``False``
        """
        data = self._filter_nones({'calories': calories, 'intensity': intensity,
                                   'personalized': personalized})
        if data and not ('calories' in data or 'intensity' in data):
            raise ValueError('Either calories or intensity is required')
        return self._resource_goal('foods/log', data)

    def water_goal(self, target=None):
        """
        Implements the following APIs

        https://dev.fitbit.com/docs/food-logging/#get-water-goal
        https://dev.fitbit.com/docs/food-logging/#update-water-goal

        Pass no arguments to get the water goal. Pass ``target`` to update it.

        Arguments:
        * ``target`` -- Target water goal in the format X.X, will be set in unit based on locale
        """
        data = self._filter_nones({'target': target})
        return self._resource_goal('foods/log/water', data)

    def time_series(self, resource, user_id=None, base_date='today',
                    period=None, end_date=None):
        """
        The time series is a LOT of methods, (documented at urls below) so they
        don't get their own method. They all follow the same patterns, and
        return similar formats.

        Taking liberty, this assumes a base_date of today, the current user,
        and a 1d period.

        https://dev.fitbit.com/docs/activity/#activity-time-series
        https://dev.fitbit.com/docs/body/#body-time-series
        https://dev.fitbit.com/docs/food-logging/#food-or-water-time-series
        https://dev.fitbit.com/docs/heart-rate/#heart-rate-time-series
        https://dev.fitbit.com/docs/sleep/#sleep-time-series
        """
        if period and end_date:
            raise TypeError("Either end_date or period can be specified, not both")

        if end_date:
            end = self._get_date_string(end_date)
        else:
            if not period in Fitbit.PERIODS:
                raise ValueError("Period must be one of %s"
                                 % ','.join(Fitbit.PERIODS))
            end = period

        url = "{0}/{1}/user/{2}/{resource}/date/{base_date}/{end}.json".format(
            *self._get_common_args(user_id),
            resource=resource,
            base_date=self._get_date_string(base_date),
            end=end
        )
        return self.make_request(url)

    def intraday_time_series(self, resource, base_date='today', detail_level='1min', start_time=None, end_time=None):
        """
        The intraday time series extends the functionality of the regular time series, but returning data at a
        more granular level for a single day, defaulting to 1 minute intervals. To access this feature, one must
        fill out the Private Support form here (see https://dev.fitbit.com/docs/help/).
        For details on the resources available and more information on how to get access, see:

        https://dev.fitbit.com/docs/activity/#get-activity-intraday-time-series
        """

        # Check that the time range is valid
        time_test = lambda t: not (t is None or isinstance(t, str) and not t)
        time_map = list(map(time_test, [start_time, end_time]))
        if not all(time_map) and any(time_map):
            raise TypeError('You must provide both the end and start time or neither')

        """
        Per
        https://dev.fitbit.com/docs/activity/#get-activity-intraday-time-series
        the detail-level is now (OAuth 2.0 ):
        either "1min" or "15min" (optional). "1sec" for heart rate.
        """
        if not detail_level in ['1sec', '1min', '15min']:
            raise ValueError("Period must be either '1sec', '1min', or '15min'")

        url = "{0}/{1}/user/-/{resource}/date/{base_date}/1d/{detail_level}".format(
            *self._get_common_args(),
            resource=resource,
            base_date=self._get_date_string(base_date),
            detail_level=detail_level
        )

        if all(time_map):
            url = url + '/time'
            for time in [start_time, end_time]:
                time_str = time
                if not isinstance(time_str, str):
                    time_str = time.strftime('%H:%M')
                url = url + ('/%s' % (time_str))

        url = url + '.json'

        return self.make_request(url)

    def activity_stats(self, user_id=None, qualifier=''):
        """
        * https://dev.fitbit.com/docs/activity/#activity-types
        * https://dev.fitbit.com/docs/activity/#get-favorite-activities
        * https://dev.fitbit.com/docs/activity/#get-recent-activity-types
        * https://dev.fitbit.com/docs/activity/#get-frequent-activities

        This implements the following methods::

            recent_activities(user_id=None, qualifier='')
            favorite_activities(user_id=None, qualifier='')
            frequent_activities(user_id=None, qualifier='')
        """
        if qualifier:
            if qualifier in Fitbit.QUALIFIERS:
                qualifier = '/%s' % qualifier
            else:
                raise ValueError("Qualifier must be one of %s"
                                 % ', '.join(Fitbit.QUALIFIERS))
        else:
            qualifier = ''

        url = "{0}/{1}/user/{2}/activities{qualifier}.json".format(
            *self._get_common_args(user_id),
            qualifier=qualifier
        )
        return self.make_request(url)

    def _food_stats(self, user_id=None, qualifier=''):
        """
        This builds the convenience methods on initialization::

            recent_foods(user_id=None, qualifier='')
            favorite_foods(user_id=None, qualifier='')
            frequent_foods(user_id=None, qualifier='')

        * https://dev.fitbit.com/docs/food-logging/#get-favorite-foods
        * https://dev.fitbit.com/docs/food-logging/#get-frequent-foods
        * https://dev.fitbit.com/docs/food-logging/#get-recent-foods
        """
        url = "{0}/{1}/user/{2}/foods/log/{qualifier}.json".format(
            *self._get_common_args(user_id),
            qualifier=qualifier
        )
        return self.make_request(url)

    def add_favorite_activity(self, activity_id):
        """
        https://dev.fitbit.com/docs/activity/#add-favorite-activity
        """
        url = "{0}/{1}/user/-/activities/favorite/{activity_id}.json".format(
            *self._get_common_args(),
            activity_id=activity_id
        )
        return self.make_request(url, method='POST')

    def log_activity(self, data):
        """
        https://dev.fitbit.com/docs/activity/#log-activity
        """
        url = "{0}/{1}/user/-/activities.json".format(*self._get_common_args())
        return self.make_request(url, data=data)

    def delete_favorite_activity(self, activity_id):
        """
        https://dev.fitbit.com/docs/activity/#delete-favorite-activity
        """
        url = "{0}/{1}/user/-/activities/favorite/{activity_id}.json".format(
            *self._get_common_args(),
            activity_id=activity_id
        )
        return self.make_request(url, method='DELETE')

    def add_favorite_food(self, food_id):
        """
        https://dev.fitbit.com/docs/food-logging/#add-favorite-food
        """
        url = "{0}/{1}/user/-/foods/log/favorite/{food_id}.json".format(
            *self._get_common_args(),
            food_id=food_id
        )
        return self.make_request(url, method='POST')

    def delete_favorite_food(self, food_id):
        """
        https://dev.fitbit.com/docs/food-logging/#delete-favorite-food
        """
        url = "{0}/{1}/user/-/foods/log/favorite/{food_id}.json".format(
            *self._get_common_args(),
            food_id=food_id
        )
        return self.make_request(url, method='DELETE')

    def create_food(self, data):
        """
        https://dev.fitbit.com/docs/food-logging/#create-food
        """
        url = "{0}/{1}/user/-/foods.json".format(*self._get_common_args())
        return self.make_request(url, data=data)

    def get_meals(self):
        """
        https://dev.fitbit.com/docs/food-logging/#get-meals
        """
        url = "{0}/{1}/user/-/meals.json".format(*self._get_common_args())
        return self.make_request(url)

    def get_devices(self):
        """
		https://dev.fitbit.com/docs/devices/#get-devices
        """
        url = "{0}/{1}/user/-/devices.json".format(*self._get_common_args())
        return self.make_request(url)

    def get_alarms(self, device_id):
        """
        https://dev.fitbit.com/docs/devices/#get-alarms
        """
        url = "{0}/{1}/user/-/devices/tracker/{device_id}/alarms.json".format(
            *self._get_common_args(),
            device_id=device_id
        )
        return self.make_request(url)

    def add_alarm(self, device_id, alarm_time, week_days, recurring=False,
                  enabled=True, label=None, snooze_length=None,
                  snooze_count=None, vibe='DEFAULT'):
        """
        https://dev.fitbit.com/docs/devices/#add-alarm
        alarm_time should be a timezone aware datetime object.
        """
        url = "{0}/{1}/user/-/devices/tracker/{device_id}/alarms.json".format(
            *self._get_common_args(),
            device_id=device_id
        )
        alarm_time = alarm_time.strftime("%H:%M%z")
        # Check week_days list
        if not isinstance(week_days, list):
            raise ValueError("Week days needs to be a list")
        for day in week_days:
            if day not in self.WEEK_DAYS:
                raise ValueError("Incorrect week day %s. see WEEK_DAY_LIST." % day)
        data = {
            'time': alarm_time,
            'weekDays': week_days,
            'recurring': recurring,
            'enabled': enabled,
            'vibe': vibe
        }
        if label:
            data['label'] = label
        if snooze_length:
            data['snoozeLength'] = snooze_length
        if snooze_count:
            data['snoozeCount'] = snooze_count
        return self.make_request(url, data=data, method="POST")
        # return

    def update_alarm(self, device_id, alarm_id, alarm_time, week_days, recurring=False, enabled=True, label=None,
                     snooze_length=None, snooze_count=None, vibe='DEFAULT'):
        """
        https://dev.fitbit.com/docs/devices/#update-alarm
        alarm_time should be a timezone aware datetime object.
        """
        # TODO Refactor with create_alarm. Tons of overlap.
        # Check week_days list
        if not isinstance(week_days, list):
            raise ValueError("Week days needs to be a list")
        for day in week_days:
            if day not in self.WEEK_DAYS:
                raise ValueError("Incorrect week day %s. see WEEK_DAY_LIST." % day)
        url = "{0}/{1}/user/-/devices/tracker/{device_id}/alarms/{alarm_id}.json".format(
            *self._get_common_args(),
            device_id=device_id,
            alarm_id=alarm_id
        )
        alarm_time = alarm_time.strftime("%H:%M%z")

        data = {
            'time': alarm_time,
            'weekDays': week_days,
            'recurring': recurring,
            'enabled': enabled,
            'vibe': vibe
        }
        if label:
            data['label'] = label
        if snooze_length:
            data['snoozeLength'] = snooze_length
        if snooze_count:
            data['snoozeCount'] = snooze_count
        return self.make_request(url, data=data, method="POST")
        # return

    def delete_alarm(self, device_id, alarm_id):
        """
        https://dev.fitbit.com/docs/devices/#delete-alarm
        """
        url = "{0}/{1}/user/-/devices/tracker/{device_id}/alarms/{alarm_id}.json".format(
            *self._get_common_args(),
            device_id=device_id,
            alarm_id=alarm_id
        )
        return self.make_request(url, method="DELETE")

    def get_sleep(self, date):
        """
        https://dev.fitbit.com/docs/sleep/#get-sleep-logs
        date should be a datetime.date object.
        """
        url = "{0}/{1}/user/-/sleep/date/{year}-{month}-{day}.json".format(
            *self._get_common_args(),
            year=date.year,
            month=date.month,
            day=date.day
        )
        return self.make_request(url)

    def log_sleep(self, start_time, duration):
        """
        https://dev.fitbit.com/docs/sleep/#log-sleep
        start time should be a datetime object. We will be using the year, month, day, hour, and minute.
        """
        data = {
            'startTime': start_time.strftime("%H:%M"),
            'duration': duration,
            'date': start_time.strftime("%Y-%m-%d"),
        }
        url = "{0}/{1}/user/-/sleep.json".format(*self._get_common_args())
        return self.make_request(url, data=data, method="POST")

    def activities_list(self):
        """
        https://dev.fitbit.com/docs/activity/#browse-activity-types
        """
        url = "{0}/{1}/activities.json".format(*self._get_common_args())
        return self.make_request(url)

    def activity_detail(self, activity_id):
        """
        https://dev.fitbit.com/docs/activity/#get-activity-type
        """
        url = "{0}/{1}/activities/{activity_id}.json".format(
            *self._get_common_args(),
            activity_id=activity_id
        )
        return self.make_request(url)

    def search_foods(self, query):
        """
        https://dev.fitbit.com/docs/food-logging/#search-foods
        """
        url = "{0}/{1}/foods/search.json?{encoded_query}".format(
            *self._get_common_args(),
            encoded_query=urlencode({'query': query})
        )
        return self.make_request(url)

    def food_detail(self, food_id):
        """
        https://dev.fitbit.com/docs/food-logging/#get-food
        """
        url = "{0}/{1}/foods/{food_id}.json".format(
            *self._get_common_args(),
            food_id=food_id
        )
        return self.make_request(url)

    def food_units(self):
        """
        https://dev.fitbit.com/docs/food-logging/#get-food-units
        """
        url = "{0}/{1}/foods/units.json".format(*self._get_common_args())
        return self.make_request(url)

    def get_bodyweight(self, base_date=None, user_id=None, period=None, end_date=None):
        """
        https://dev.fitbit.com/docs/body/#get-weight-logs
        base_date should be a datetime.date object (defaults to today),
        period can be '1d', '7d', '30d', '1w', '1m', '3m', '6m', '1y', 'max' or None
        end_date should be a datetime.date object, or None.

        You can specify period or end_date, or neither, but not both.
        """
        return self._get_body('weight', base_date, user_id, period, end_date)

    def get_bodyfat(self, base_date=None, user_id=None, period=None, end_date=None):
        """
        https://dev.fitbit.com/docs/body/#get-body-fat-logs
        base_date should be a datetime.date object (defaults to today),
        period can be '1d', '7d', '30d', '1w', '1m', '3m', '6m', '1y', 'max' or None
        end_date should be a datetime.date object, or None.

        You can specify period or end_date, or neither, but not both.
        """
        return self._get_body('fat', base_date, user_id, period, end_date)

    def _get_body(self, type_, base_date=None, user_id=None, period=None,
                  end_date=None):
        if not base_date:
            base_date = datetime.date.today()

        if period and end_date:
            raise TypeError("Either end_date or period can be specified, not both")

        base_date_string = self._get_date_string(base_date)

        kwargs = {'type_': type_}
        base_url = "{0}/{1}/user/{2}/body/log/{type_}/date/{date_string}.json"
        if period:
            if not period in Fitbit.PERIODS:
                raise ValueError("Period must be one of %s" %
                                 ','.join(Fitbit.PERIODS))
            kwargs['date_string'] = '/'.join([base_date_string, period])
        elif end_date:
            end_string = self._get_date_string(end_date)
            kwargs['date_string'] = '/'.join([base_date_string, end_string])
        else:
            kwargs['date_string'] = base_date_string

        url = base_url.format(*self._get_common_args(user_id), **kwargs)
        return self.make_request(url)

    def get_friends(self, user_id=None):
        """
        https://dev.fitbit.com/docs/friends/#get-friends
        """
        url = "{0}/{1}/user/{2}/friends.json".format(*self._get_common_args(user_id))
        return self.make_request(url)

    def get_friends_leaderboard(self, period):
        """
        https://dev.fitbit.com/docs/friends/#get-friends-leaderboard
        """
        if not period in ['7d', '30d']:
            raise ValueError("Period must be one of '7d', '30d'")
        url = "{0}/{1}/user/-/friends/leaders/{period}.json".format(
            *self._get_common_args(),
            period=period
        )
        return self.make_request(url)

    def invite_friend(self, data):
        """
        https://dev.fitbit.com/docs/friends/#invite-friend
        """
        url = "{0}/{1}/user/-/friends/invitations.json".format(*self._get_common_args())
        return self.make_request(url, data=data)

    def invite_friend_by_email(self, email):
        """
        Convenience Method for
        https://dev.fitbit.com/docs/friends/#invite-friend
        """
        return self.invite_friend({'invitedUserEmail': email})

    def invite_friend_by_userid(self, user_id):
        """
        Convenience Method for
        https://dev.fitbit.com/docs/friends/#invite-friend
        """
        return self.invite_friend({'invitedUserId': user_id})

    def respond_to_invite(self, other_user_id, accept=True):
        """
        https://dev.fitbit.com/docs/friends/#respond-to-friend-invitation
        """
        url = "{0}/{1}/user/-/friends/invitations/{user_id}.json".format(
            *self._get_common_args(),
            user_id=other_user_id
        )
        accept = 'true' if accept else 'false'
        return self.make_request(url, data={'accept': accept})

    def accept_invite(self, other_user_id):
        """
        Convenience method for respond_to_invite
        """
        return self.respond_to_invite(other_user_id)

    def reject_invite(self, other_user_id):
        """
        Convenience method for respond_to_invite
        """
        return self.respond_to_invite(other_user_id, accept=False)

    def get_badges(self, user_id=None):
        """
        https://dev.fitbit.com/docs/friends/#badges
        """
        url = "{0}/{1}/user/{2}/badges.json".format(*self._get_common_args(user_id))
        return self.make_request(url)

    def subscription(self, subscription_id, subscriber_id, collection=None,
                     method='POST'):
        """
        https://dev.fitbit.com/docs/subscriptions/
        """
        base_url = "{0}/{1}/user/-{collection}/apiSubscriptions/{end_string}.json"
        kwargs = {'collection': '', 'end_string': subscription_id}
        if collection:
            kwargs = {
                'end_string': '-'.join([subscription_id, collection]),
                'collection': '/' + collection
            }
        return self.make_request(
            base_url.format(*self._get_common_args(), **kwargs),
            method=method,
            headers={"X-Fitbit-Subscriber-id": subscriber_id}
        )

    def list_subscriptions(self, collection=''):
        """
        https://dev.fitbit.com/docs/subscriptions/#getting-a-list-of-subscriptions
        """
        url = "{0}/{1}/user/-{collection}/apiSubscriptions.json".format(
            *self._get_common_args(),
            collection='/{0}'.format(collection) if collection else ''
        )
        return self.make_request(url)
