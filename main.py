#!/usr/bin/env python
from http import client
import json
import sys

from firebase_admin import credentials, firestore
from oauth2.server import OAuth2Server
from fitbit.api import Fitbit
from persistance import firestore

def read_secrets(path):
    file = open(path)
    return json.load(file)

if __name__ == '__main__':
    secrets = read_secrets("private_assets/fitbit-oauth2-secrets.json")

    server = OAuth2Server(client_id=secrets["client_id"], client_secret=secrets["client_secret"])
    server.browser_authorize()

    profile = server.fitbit.user_profile_get()['user']
    print("\n\n--------------------------------------------------")
    print('You are authorized to access data for the user: {}'.format(profile['fullName']))
    print("--------------------------------------------------")

    heart_rate_data = server.fitbit.time_series(resource='activities/heart', period='7d')
    activities_data = server.fitbit.log_activity(data=None)

    fs = firestore.FirestoreImpl(
        'private_assets/tigerawarefitbitdev-firebase-adminsdk-1kn23-4e47246d45.json', 
        'fitbitAbs', 
        profile['encodedId'])
    fs.store_profile(profile)
    fs.store_activities(heart_rate_data, "heart_rate")
    fs.store_activities(activities_data, "activities_summary")
