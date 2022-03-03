#!/usr/bin/env python
from http import client
import json
import sys

from firebase_admin import credentials, firestore
from oauth2.server import OAuth2Server
from fitbit.api import Fitbit
from persistance import firestore
from persistance.usecase import StoreUsecase

def read_secrets(path):
    file = open(path)
    return json.load(file)

def invoke_auth(secret_path):
    secrets = read_secrets(secret_path)
    server = OAuth2Server(client_id=secrets["client_id"], client_secret=secrets["client_secret"])
    server.browser_authorize()
    return server

def get_date_range():
    # print("Insert start time (YYYY-MM-DD): ",)
    # start_date = input()
    # print("Insert end time (YYYY-MM-DD): ")
    # end_date = input()

    # return start_date, end_date
    return "today", "today"


if __name__ == '__main__':
    server = invoke_auth(secret_path="private_assets/fitbit-oauth2-secrets-user.json")
    start_date, end_date = get_date_range()
    fs = firestore.FirestoreImpl(
        certificate_path='private_assets/tigerawarefitbitdev-firebase-adminsdk-1kn23-4e47246d45.json', 
        collect_name='userWithPersonalApp')
    usecase = StoreUsecase(server.fitbit, fs, start_date, end_date)
    usecase.get_profile()
    usecase.get_intraday()

    # heart_rate_data = server.fitbit.time_series(resource='activities/heart', period='7d')
    # activities_data = server.fitbit.log_activity(data=None)
    # fs.store_activities(heart_rate_data, "heart_rate")
    # fs.store_activities(activities_data, "activities_summary")
