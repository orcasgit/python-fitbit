#!/usr/bin/env python
import fitbit
import configparser
import datetime
import os
import time
import json
from fitbit.exceptions import HTTPTooManyRequests
from fitbit.exceptions import HTTPUnauthorized
import argparse
import sys

DUMP_DIR = 'fitbit-dumps'


def mkdate(datestr):
    try:
        fulltime = time.strptime(datestr, '%Y-%m-%d')
        return datetime.date(fulltime.tm_year, fulltime.tm_mon, fulltime.tm_mday)
    except ValueError:
        raise argparse.ArgumentTypeError(datestr + ' is not a proper date string')


def logmsg(msg):
    time = datetime.datetime.now()
    print("[%04i/%02i/%02i %02i:%02i:%02i]: %s" % (time.year, time.month, time.day, time.hour, time.minute, time.second, msg))


def dump_to_str(data):
    return "\n".join(["%s,%s" % (str(d['time']), d['value']) for d in data])


def dump_to_json_file(data_type, date, data):
    directory = "%s/%i/%s" % (DUMP_DIR, date.year, date)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open("%s/%s.json" % (directory, data_type), "w") as f:
        f.write(json.dumps(data, indent=2))
    time.sleep(1)


def previously_dumped(date):
    return os.path.isdir("%s/%i/%s" % (DUMP_DIR, date.year, date))


def dump_day(c, date):
    steps_data = c.intraday_time_series('activities/steps', base_date=date, detail_level='1min')
    steps = steps_data['activities-steps']
    dump_to_json_file("steps", date, steps_data)

    cals_data = c.intraday_time_series('activities/calories', base_date=date, detail_level='1min', start_time=None, end_time=None)
    dump_to_json_file("calories", date, cals_data)

    distance_data = c.intraday_time_series('activities/distance', base_date=date, detail_level='1min', start_time=None, end_time=None)
    dump_to_json_file("distance", date, distance_data)

    floor_data = c.intraday_time_series('activities/floors', base_date=date, detail_level='1min', start_time=None, end_time=None)
    dump_to_json_file("floors", date, floor_data)

    heart_data =c.intraday_time_series('activities/heart', base_date=date, detail_level='1min', start_time=None, end_time=None)
    dump_to_json_file("heart", date, heart_data)

    sleep_data = c.get_sleep(date)
    dump_to_json_file("sleep", date, sleep_data)

    weight_data = c.get_bodyweight(date)
    dump_to_json_file("weight", date, weight_data)

    foods_data = c.foods_log(date)
    dump_to_json_file("foods", date, foods_data)

    water_data = c.foods_log_water(date)
    dump_to_json_file("water", date, water_data)
    return True


def update_tokens(token_dict):
    logmsg('updating tokens')
    global CI_access_token
    global CI_refresh_token
    global CI_expires_at
    CI_access_token = token_dict['access_token']
    CI_refresh_token = token_dict['refresh_token']
    CI_expires_at = token_dict['expires_at']

    logmsg('updating config file')
    global config_parser
    config_parser['Login Parameters']['ACCESS_TOKEN'] = CI_access_token
    config_parser['Login Parameters']['REFRESH_TOKEN'] = CI_refresh_token
    config_parser['Login Parameters']['EXPIRES_AT'] = str(CI_expires_at)
    with open('fitbit.ini', 'w') as configfile:
        config_parser.write(configfile)

config_parser = configparser.ConfigParser()

# assuming that we wrote the data from gather_keys_oauth2.py to this ini file...
config_parser.read('fitbit.ini')
CI_id = config_parser.get('Login Parameters', 'CLIENT_ID')
CI_client_secret = config_parser.get('Login Parameters', 'CLIENT_SECRET')
CI_access_token = config_parser.get('Login Parameters', 'ACCESS_TOKEN')
CI_refresh_token = config_parser.get('Login Parameters', 'REFRESH_TOKEN')
CI_expires_at = float(config_parser.get('Login Parameters', 'EXPIRES_AT'))
authd_client = fitbit.Fitbit(CI_id, CI_client_secret, oauth2=True, access_token=CI_access_token, refresh_token=CI_refresh_token, expires_at=CI_expires_at, refresh_cb=update_tokens)

date = datetime.date.today()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dump all fitbit data.')
    parser.add_argument('-d', '--date', type=mkdate)
    ns = parser.parse_args()
    if not ns.date is None:
        date = ns.date

pause_between_days = 60
days_since_last_expiry = 0
api_timeouts = 0
api_server_errors = 0

# to handle: fitbit.exceptions.HTTPServerError: <Response [504]>
while not previously_dumped(date):
    logmsg('dumping: {}'.format(date))
    try:
        r = dump_day(authd_client, date)
    except HTTPTooManyRequests as e:
        curtime = datetime.datetime.now()
        restart_time = datetime.datetime.time(curtime + datetime.timedelta(seconds=e.retry_after_secs))
        logmsg('too many requests! waiting {0} seconds, at {1}'.format(e.retry_after_secs, restart_time))
        pause_between_days = int(pause_between_days + 1 + (e.retry_after_secs/days_since_last_expiry))
        days_since_last_expiry = 0
        logmsg('new pause between days %i seconds' % pause_between_days)
        time.sleep(e.retry_after_secs + 10)
    except HTTPUnauthorized as e:
        logmsg('token has expired, exiting. start with new date: {}'.format(date))
        sys.exit(1)
    except fitbit.exceptions.Timeout as t:
        if api_timeouts > 5:
            logmsg('too many timeouts in a row. exiting')
            sys.exit(1)
        logmsg('Timeout error: pausing and retrying in {} seconds'.format(pause_between_days))
        api_timeouts += 1
        time.sleep(pause_between_days)
    except fitbit.exceptions.HTTPServerError as e:
        print('server error!')
        print(e.args)
        if api_server_errors > 5:
            logmsg('too many Server Errors in a row. exiting')
            sys.exit(1)
        logmsg('Server error: pausing and retrying in {} seconds'.format(pause_between_days))
        api_server_errors += 1
        time.sleep(pause_between_days)
    else:
        days_since_last_expiry += 1
        date -= datetime.timedelta(days=1)
        api_timeouts = 0
        api_server_errors = 0
        if not r:
            break
        # wait a minute just to not throttle the API since we can only do 150
        # calls per hour
        time.sleep(pause_between_days)

# Always redump the last dumped day because we may have dumped it before the day was finished.
dump_day(authd_client, date)
