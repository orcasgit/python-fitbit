# -*- coding: utf-8 -*-
import oauth2 as oauth
import requests
import urlparse
import json
import datetime
import urllib

from fitbit.exceptions import (BadResponse, DeleteError, HTTPBadRequest,
                               HTTPUnauthorized, HTTPForbidden,
                               HTTPServerError, HTTPConflict, HTTPNotFound)
from fitbit.utils import curry


class FitbitConsumer(oauth.Consumer):
    pass


# example client using httplib with headers
class FitbitOauthClient(oauth.Client):
    API_ENDPOINT = "https://api.fitbit.com"
    AUTHORIZE_ENDPOINT = "https://www.fitbit.com"
    API_VERSION = 1
    _signature_method = oauth.SignatureMethod_HMAC_SHA1()

    request_token_url = "%s/oauth/request_token" % API_ENDPOINT
    access_token_url = "%s/oauth/access_token" % API_ENDPOINT
    authorization_url = "%s/oauth/authorize" % AUTHORIZE_ENDPOINT

    def __init__(self, consumer_key, consumer_secret, user_key=None,
                 user_secret=None, user_id=None, *args, **kwargs):
        if user_key and user_secret:
            self._token = oauth.Token(user_key, user_secret)
        else:
            # This allows public calls to be made
            self._token = None
        if user_id:
            self.user_id = user_id
        self._consumer = FitbitConsumer(consumer_key, consumer_secret)
        super(FitbitOauthClient, self).__init__(self._consumer, *args, **kwargs)

    def _request(self, method, url, **kwargs):
        """
        A simple wrapper around requests.
        """
        return requests.request(method, url, **kwargs)

    def make_request(self, url, data={}, method=None, **kwargs):
        """
        Builds and makes the Oauth Request, catches errors

        https://wiki.fitbit.com/display/API/API+Response+Format+And+Errors
        """
        if not method:
            method = 'POST' if data else 'GET'
        request = oauth.Request.from_consumer_and_token(self._consumer, self._token, http_method=method, http_url=url, parameters=data)
        request.sign_request(self._signature_method, self._consumer,
                             self._token)
        response = self._request(method, url, data=data,
                                 headers=request.to_header())

        if response.status_code == 401:
            raise HTTPUnauthorized(response)
        elif response.status_code == 403:
            raise HTTPForbidden(response)
        elif response.status_code == 404:
            raise HTTPNotFound(response)
        elif response.status_code == 409:
            raise HTTPConflict(response)
        elif response.status_code >= 500:
            raise HTTPServerError(response)
        elif response.status_code >= 400:
            raise HTTPBadRequest(response)
        return response

    def fetch_request_token(self, parameters=None):
        """
        Step 1 of getting authorized to access a user's data at fitbit: this
        makes a signed request to fitbit to get a token to use in the next
        step.  Returns that token.

        Set parameters['oauth_callback'] to a URL and when the user has
        granted us access at the fitbit site, fitbit will redirect them to the URL
        you passed.  This is how we get back the magic verifier string from fitbit
        if we're a web app. If we don't pass it, then fitbit will just display
        the verifier string for the user to copy and we'll have to ask them to
        paste it for us and read it that way.
        """

        """
        via headers
        -> OAuthToken

        Providing 'oauth_callback' parameter in the Authorization header of
        request_token_url request, will have priority over the dev.fitbit.com
        settings, ie. parameters = {'oauth_callback': 'callback_url'}
        """

        request = oauth.Request.from_consumer_and_token(
            self._consumer,
            http_url=self.request_token_url,
            parameters=parameters
        )
        request.sign_request(self._signature_method, self._consumer, None)
        response = self._request(request.method, self.request_token_url,
                                 headers=request.to_header())
        return oauth.Token.from_string(response.content)

    def authorize_token_url(self, token):
        """Step 2: Given the token returned by fetch_request_token(), return
        the URL the user needs to go to in order to grant us authorization
        to look at their data.  Then redirect the user to that URL, open their
        browser to it, or tell them to copy the URL into their browser.
        """
        request = oauth.Request.from_token_and_callback(
            token=token,
            http_url=self.authorization_url
        )
        return request.to_url()

    #def authorize_token(self, token):
    #    # via url
    #    # -> typically just some okay response
    #    request = oauth.Request.from_token_and_callback(token=token,
    #                                         http_url=self.authorization_url)
    #    response = self._request(request.method, request.to_url(),
    #                                             headers=request.to_header())
    #    return response.content

    def fetch_access_token(self, token, verifier):
        """Step 4: Given the token from step 1, and the verifier from step 3 (see step 2),
        calls fitbit again and returns an access token object.  Extract .key and .secret
        from that and save them, then pass them as user_key and user_secret in future
        API calls to fitbit to get this user's data.
        """
        request = oauth.Request.from_consumer_and_token(self._consumer, token, http_method='POST', http_url=self.access_token_url, parameters={'oauth_verifier': verifier})
        body = "oauth_verifier=%s" % verifier
        response = self._request('POST', self.access_token_url, data=body,
                                 headers=request.to_header())
        if response.status_code != 200:
            # TODO custom exceptions
            raise Exception("Invalid response %s." % response.content)
        params = urlparse.parse_qs(response.content, keep_blank_values=False)
        self.user_id = params['encoded_user_id'][0]
        self._token = oauth.Token.from_string(response.content)
        return self._token


class Fitbit(object):
    US = 'en_US'
    METRIC = 'en_UK'

    API_ENDPOINT = "https://api.fitbit.com"
    API_VERSION = 1

    _resource_list = [
        'body',
        'activities',
        'foods',
        'water',
        'sleep',
        'heart',
        'bp',
        'glucose',
    ]

    _qualifiers = [
        'recent',
        'favorite',
        'frequent',
    ]

    def __init__(self, consumer_key, consumer_secret, system=US, **kwargs):
        self.client = FitbitOauthClient(consumer_key, consumer_secret, **kwargs)
        self.SYSTEM = system

        # All of these use the same patterns, define the method for accessing
        # creating and deleting records once, and use curry to make individual
        # Methods for each
        for resource in self._resource_list:
            setattr(self, resource, curry(self._COLLECTION_RESOURCE, resource))

            if resource not in ['body', 'glucose']:
                # Body and Glucose entries are not currently able to be deleted
                setattr(self, 'delete_%s' % resource, curry(
                    self._DELETE_COLLECTION_RESOURCE, resource))

        for qualifier in self._qualifiers:
            setattr(self, '%s_activities' % qualifier, curry(self.activity_stats, qualifier=qualifier))
            setattr(self, '%s_foods' % qualifier, curry(self._food_stats,
                                                        qualifier=qualifier))

    def make_request(self, *args, **kwargs):
        ##@ This should handle data level errors, improper requests, and bad
        # serialization
        headers = kwargs.get('headers', {})
        headers.update({'Accept-Language': self.SYSTEM})
        kwargs['headers'] = headers

        method = kwargs.get('method', 'POST' if 'data' in kwargs else 'GET')
        response = self.client.make_request(*args, **kwargs)

        if response.status_code == 202:
            return True
        if method == 'DELETE':
            if response.status_code == 204:
                return True
            else:
                raise DeleteError(response)
        try:
            rep = json.loads(response.content)
        except ValueError:
            raise BadResponse

        return rep

    def user_profile_get(self, user_id=None):
        """
        Get a user profile. You can get other user's profile information
        by passing user_id, or you can get the current user's by not passing
        a user_id

        .. note:
            This is not the same format that the GET comes back in, GET requests
            are wrapped in {'user': <dict of user data>}

        https://wiki.fitbit.com/display/API/API-Get-User-Info
        """
        if user_id is None:
            user_id = "-"
        url = "%s/%s/user/%s/profile.json" % (self.API_ENDPOINT,
                                              self.API_VERSION, user_id)
        return self.make_request(url)

    def user_profile_update(self, data):
        """
        Set a user profile. You can set your user profile information by
        passing a dictionary of attributes that will be updated.

        .. note:
            This is not the same format that the GET comes back in, GET requests
            are wrapped in {'user': <dict of user data>}

        https://wiki.fitbit.com/display/API/API-Update-User-Info
        """
        url = "%s/%s/user/-/profile.json" % (self.API_ENDPOINT,
                                              self.API_VERSION)
        return self.make_request(url, data)

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
            foods(date=None, user_id=None, data=None)
            water(date=None, user_id=None, data=None)
            sleep(date=None, user_id=None, data=None)
            heart(date=None, user_id=None, data=None)
            bp(date=None, user_id=None, data=None)

        * https://wiki.fitbit.com/display/API/Fitbit+Resource+Access+API
        """

        if not date:
            date = datetime.date.today()
        if not user_id:
            user_id = '-'
        if not isinstance(date, basestring):
            date = date.strftime('%Y-%m-%d')

        if not data:
            url = "%s/%s/user/%s/%s/date/%s.json" % (
                self.API_ENDPOINT,
                self.API_VERSION,
                user_id,
                resource,
                date,
            )
        else:
            data['date'] = date
            url = "%s/%s/user/%s/%s.json" % (
                self.API_ENDPOINT,
                self.API_VERSION,
                user_id,
                resource,
            )
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
            delete_foods(log_id)
            delete_water(log_id)
            delete_sleep(log_id)
            delete_heart(log_id)
            delete_bp(log_id)

        """
        url = "%s/%s/user/-/%s/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            resource,
            log_id,
        )
        response = self.make_request(url, method='DELETE')
        return response

    def time_series(self, resource, user_id=None, base_date='today',
                    period=None, end_date=None):
        """
        The time series is a LOT of methods, (documented at url below) so they
        don't get their own method. They all follow the same patterns, and
        return similar formats.

        Taking liberty, this assumes a base_date of today, the current user,
        and a 1d period.

        https://wiki.fitbit.com/display/API/API-Get-Time-Series
        """
        if not user_id:
            user_id = '-'

        if period and end_date:
            raise TypeError("Either end_date or period can be specified, not both")

        if end_date:
            if not isinstance(end_date, basestring):
                end = end_date.strftime('%Y-%m-%d')
            else:
                end = end_date
        else:
            if not period in ['1d', '7d', '30d', '1w', '1m', '3m', '6m', '1y', 'max']:
                raise ValueError("Period must be one of '1d', '7d', '30d', '1w', '1m', '3m', '6m', '1y', 'max'")
            end = period

        if not isinstance(base_date, basestring):
            base_date = base_date.strftime('%Y-%m-%d')

        url = "%s/%s/user/%s/%s/date/%s/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            user_id,
            resource,
            base_date,
            end
        )
        return self.make_request(url)

    def activity_stats(self, user_id=None, qualifier=''):
        """
        * https://wiki.fitbit.com/display/API/API-Get-Activity-Stats
        * https://wiki.fitbit.com/display/API/API-Get-Favorite-Activities
        * https://wiki.fitbit.com/display/API/API-Get-Recent-Activities
        * https://wiki.fitbit.com/display/API/API-Get-Frequent-Activities

        This implements the following methods::

            recent_activities(user_id=None, qualifier='')
            favorite_activities(user_id=None, qualifier='')
            frequent_activities(user_id=None, qualifier='')
        """
        if not user_id:
            user_id = '-'

        if qualifier:
            if qualifier in self._qualifiers:
                qualifier = '/%s' % qualifier
            else:
                raise ValueError("Qualifier must be one of %s"
                    % ', '.join(self._qualifiers))
        else:
            qualifier = ''

        url = "%s/%s/user/%s/activities%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            user_id,
            qualifier,
        )
        return self.make_request(url)

    def _food_stats(self, user_id=None, qualifier=''):
        """
        This builds the convenience methods on initialization::

            recent_foods(user_id=None, qualifier='')
            favorite_foods(user_id=None, qualifier='')
            frequent_foods(user_id=None, qualifier='')

        * https://wiki.fitbit.com/display/API/API-Get-Recent-Foods
        * https://wiki.fitbit.com/display/API/API-Get-Frequent-Foods
        * https://wiki.fitbit.com/display/API/API-Get-Favorite-Foods
        """
        if not user_id:
            user_id = '-'

        url = "%s/%s/user/%s/foods/log/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            user_id,
            qualifier,
        )
        return self.make_request(url)

    def add_favorite_activity(self, activity_id):
        """
        https://wiki.fitbit.com/display/API/API-Add-Favorite-Activity
        """
        url = "%s/%s/user/-/activities/favorite/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            activity_id,
        )
        return self.make_request(url, method='POST')

    def delete_favorite_activity(self, activity_id):
        """
        https://wiki.fitbit.com/display/API/API-Delete-Favorite-Activity
        """
        url = "%s/%s/user/-/activities/favorite/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            activity_id,
        )
        return self.make_request(url, method='DELETE')

    def add_favorite_food(self, food_id):
        """
        https://wiki.fitbit.com/display/API/API-Add-Favorite-Food
        """
        url = "%s/%s/user/-/foods/log/favorite/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            food_id,
        )
        return self.make_request(url, method='POST')

    def delete_favorite_food(self, food_id):
        """
        https://wiki.fitbit.com/display/API/API-Delete-Favorite-Food
        """
        url = "%s/%s/user/-/foods/log/favorite/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            food_id,
        )
        return self.make_request(url, method='DELETE')

    def create_food(self, data):
        """
        https://wiki.fitbit.com/display/API/API-Create-Food
        """
        url = "%s/%s/user/-/foods.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
        )
        return self.make_request(url, data=data)

    def get_meals(self):
        """
        https://wiki.fitbit.com/display/API/API-Get-Meals
        """
        url = "%s/%s/user/-/meals.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
        )
        return self.make_request(url)

    def get_devices(self):
        """
        https://wiki.fitbit.com/display/API/API-Get-Devices
        """
        url = "%s/%s/user/-/devices.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
        )
        return self.make_request(url)

    def activities_list(self):
        """
        https://wiki.fitbit.com/display/API/API-Browse-Activities
        """
        url = "%s/%s/activities.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
        )
        return self.make_request(url)

    def activity_detail(self, activity_id):
        """
        https://wiki.fitbit.com/display/API/API-Get-Activity
        """
        url = "%s/%s/activities/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            activity_id
        )
        return self.make_request(url)

    def search_foods(self, query):
        """
        https://wiki.fitbit.com/display/API/API-Search-Foods
        """
        url = "%s/%s/foods/search.json?%s" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            urllib.urlencode({'query': query})
        )
        return self.make_request(url)

    def food_detail(self, food_id):
        """
        https://wiki.fitbit.com/display/API/API-Get-Food
        """
        url = "%s/%s/foods/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            food_id
        )
        return self.make_request(url)

    def food_units(self):
        """
        https://wiki.fitbit.com/display/API/API-Get-Food-Units
        """
        url = "%s/%s/foods/units.json" % (
            self.API_ENDPOINT,
            self.API_VERSION
        )
        return self.make_request(url)

    def get_friends(self, user_id=None):
        """
        https://wiki.fitbit.com/display/API/API-Get-Friends
        """
        if not user_id:
            user_id = '-'
        url = "%s/%s/user/%s/friends.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            user_id
        )
        return self.make_request(url)

    def get_friends_leaderboard(self, period):
        """
        https://wiki.fitbit.com/display/API/API-Get-Friends-Leaderboard
        """
        if not period in ['7d', '30d']:
            raise ValueError("Period must be one of '7d', '30d'")
        url = "%s/%s/user/-/friends/leaders/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            period
        )
        return self.make_request(url)

    def invite_friend(self, data):
        """
        https://wiki.fitbit.com/display/API/API-Create-Invite
        """
        url = "%s/%s/user/-/friends/invitations.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
        )
        return self.make_request(url, data=data)

    def invite_friend_by_email(self, email):
        """
        Convenience Method for
        https://wiki.fitbit.com/display/API/API-Create-Invite
        """
        return self.invite_friend({'invitedUserEmail': email})

    def invite_friend_by_userid(self, user_id):
        """
        Convenience Method for
        https://wiki.fitbit.com/display/API/API-Create-Invite
        """
        return self.invite_friend({'invitedUserId': user_id})

    def respond_to_invite(self, other_user_id, accept=True):
        """
        https://wiki.fitbit.com/display/API/API-Accept-Invite
        """
        url = "%s/%s/user/-/friends/invitations/%s.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            other_user_id,
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

    def subscription(self, subscription_id, subscriber_id, collection=None,
                     method='POST'):
        """
        https://wiki.fitbit.com/display/API/Fitbit+Subscriptions+API
        """
        if not collection:
            url = "%s/%s/user/-/apiSubscriptions/%s.json" % (
                self.API_ENDPOINT,
                self.API_VERSION,
                subscription_id
            )
        else:
            url = "%s/%s/user/-/%s/apiSubscriptions/%s-%s.json" % (
                self.API_ENDPOINT,
                self.API_VERSION,
                collection,
                subscription_id,
                collection
            )
        return self.make_request(
            url,
            method=method,
            headers={"X-Fitbit-Subscriber-id": subscriber_id}
        )

    def list_subscriptions(self, collection=''):
        """
        https://wiki.fitbit.com/display/API/Fitbit+Subscriptions+API
        """
        if collection:
            collection = '/%s' % collection
        url = "%s/%s/user/-%s/apiSubscriptions.json" % (
            self.API_ENDPOINT,
            self.API_VERSION,
            collection,
        )
        return self.make_request(url)

    @classmethod
    def from_oauth_keys(self, consumer_key, consumer_secret, user_key=None,
                        user_secret=None, user_id=None, system=US):
        client = FitbitOauthClient(consumer_key, consumer_secret, user_key,
                                   user_secret, user_id)
        return self(client, system)
