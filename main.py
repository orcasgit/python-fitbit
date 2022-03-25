#!/usr/bin/env python
from http import client
import json
import os
import sys
from tracemalloc import start

from firebase_admin import credentials, firestore
from fitbit.fitbit import Fitbit
from repository import firestore, realtime_database
from repository.csv import Csv
from repository.gcloud import GoogleCloud
from repository.gcloud_repository import GoogleCloudRepository
from repository.repository import Repository
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials
from oauthlib.oauth2.rfc6749.errors import MismatchingStateError, MissingTokenError

def read_secrets(path):
    file = open(path)
    return json.load(file)

def init_firebase(certificate_path, database_url):
    cred = credentials.Certificate(certificate_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url
        })

def get_date_range():
    print("\n--------------------------------------------------")
    print("Insert start time (YYYY-MM-DD): ",)
    start_date = datetime.strptime("2022-02-02", '%Y-%m-%d')
    print("Insert end time (YYYY-MM-DD): ")
    end_date = datetime.strptime("2022-02-03", '%Y-%m-%d')

    time_test = lambda t: not (t is None or isinstance(t, str) and not t)
    time_map = list(map(time_test, [start_date, end_date]))
    if not all(time_map) and any(time_map):
        raise TypeError('You must provide both the end and start time or neither')

    print("Getting data in the date ranging from {start_date} to {end_date}".format(
        start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d')))

    return start_date, end_date

def refresh(token):
    print(token)

if __name__ == '__main__':
    fitbit = Fitbit(
            client_id="2388KL",
            client_secret="4af99468fa50d289b6ca310538be7383",
            access_token="eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyMzg4S0wiLCJzdWIiOiI5VkZOR0YiLCJpc3MiOiJGaXRiaXQiLCJ0eXAiOiJhY2Nlc3NfdG9rZW4iLCJzY29wZXMiOiJyc29jIHJhY3QgcnNldCBybG9jIHJ3ZWkgcmhyIHJwcm8gcm51dCByc2xlIiwiZXhwIjoxNjQ4MjA0Mjc4LCJpYXQiOjE2NDgxNzU0Nzh9.-FV3I0YDp3HGyhIiaqa-s_8GCSx0EaGbvp2PcIEs430",
            refresh_token="16b13fe1f5eff34bddb48418cd758a7887f960807f1d774cd8bf9dfc1ea43fdf",
            timeout=10,
            refresh_cb=refresh
        )

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/reyvababtista/Projects/python-fitbit/secrets/tigerawaredev-6692e3e245ac.json"
    
    gc = GoogleCloud()
    gc_repository = GoogleCloudRepository(gc=gc)
    firebase_credentials = gc_repository.get_firebase_credential("tigerawaredev")
    firebase_realtime_db_url = gc_repository.get_realtime_db_url("tigerawaredev")
    print(firebase_credentials)
    print(firebase_realtime_db_url)
    init_firebase(certificate_path=firebase_credentials, database_url=firebase_realtime_db_url)
    
    start_date, end_date = get_date_range()
    root = 'fitbit'
    fs = firestore.Firestore(collect_name=root)
    rdb = realtime_database.Realtime(root=root)
    csv = Csv()
    repository = Repository(fitbit, fs, csv, rdb, start_date, end_date)
    repository.get_profile()
    # repository.get_intraday()
    # repository.get_time_series()
