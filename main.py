#!/usr/bin/env python
from http import client
import json
import sys

from firebase_admin import credentials, firestore
from oauth2.server import OAuth2Server
from fitbit.api import Fitbit
from persistance import firestore
from persistance.usecase import StoreUsecase
from datetime import datetime

def read_secrets(path):
    file = open(path)
    return json.load(file)

def invoke_auth(secret_path):
    secrets = read_secrets(secret_path)
    server = OAuth2Server(client_id=secrets["client_id"], client_secret=secrets["client_secret"])
    server.browser_authorize()
    return server

def get_date_range():
    print("\n--------------------------------------------------")
    today = datetime.today().strftime('%Y-%m-%d')
    print("Insert start time (YYYY-MM-DD): ",)
    start_date = today #input()
    print("Insert end time (YYYY-MM-DD): ")
    end_date = today #input()

    time_test = lambda t: not (t is None or isinstance(t, str) and not t)
    time_map = list(map(time_test, [start_date, end_date]))
    if not all(time_map) and any(time_map):
        raise TypeError('You must provide both the end and start time or neither')

    print("Getting data in the date ranging from {start_date} to {end_date}".format(
        start_date=start_date, end_date=end_date))

    return start_date, end_date

if __name__ == '__main__':
    server = invoke_auth(secret_path="private_assets/fitbit-oauth2-secrets-user.json")
    start_date, end_date = get_date_range()
    fs = firestore.FirestoreImpl(
        certificate_path='private_assets/tigerawarefitbitdev-firebase-adminsdk-1kn23-4e47246d45.json', 
        collect_name='userWithPersonalApp')
    usecase = StoreUsecase(server.fitbit, fs, start_date, end_date)
    usecase.get_profile()
    # usecase.get_intraday()
    usecase.get_time_series()
