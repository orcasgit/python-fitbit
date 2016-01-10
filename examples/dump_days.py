#!/usr/bin/env python
import fitbit
import ConfigParser
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
    steps_data = c.intraday_time_series('activities/steps', base_date=date, detail_level='1min', start_time=None, end_time=None)
    steps = steps_data['activities-steps-intraday']['dataset']
    # Assume that if no steps were recorded then there is no more data
    if sum(s['value'] for s in steps) == 0:
        return False

    dump_to_json_file("steps", date, steps_data)

    cals_data = c.intraday_time_series('activities/calories', base_date=date, detail_level='1min', start_time=None, end_time=None)
    dump_to_json_file("calories", date, cals_data)

    distance_data = c.intraday_time_series('activities/distance', base_date=date, detail_level='1min', start_time=None, end_time=None)
    dump_to_json_file("distance", date, distance_data)

    floor_data = c.intraday_time_series('activities/floors', base_date=date, detail_level='1min', start_time=None, end_time=None)
    dump_to_json_file("floors", date, floor_data)

    sleep_data = c.get_sleep(date)
    dump_to_json_file("sleep", date, sleep_data)
    return True


parser = ConfigParser.SafeConfigParser()

# assuming that we wrote the data from gather_keys_oauth2.py to this ini file...
parser.read('fitbit.ini')
CI_id = parser.get('Login Parameters', 'CLIENT_ID')
CI_client_secret = parser.get('Login Parameters', 'CLIENT_SECRET')
CI_access_token = parser.get('Login Parameters', 'ACCESS_TOKEN')
CI_refresh_token = parser.get('Login Parameters', 'REFRESH_TOKEN')
authd_client = fitbit.Fitbit(CI_id, CI_client_secret, oauth2=True, access_token=CI_access_token, refresh_token=CI_refresh_token)

date = datetime.date.today()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dump all fitbit data.')
    parser.add_argument('-d', '--date', type=mkdate)
    ns = parser.parse_args()
    if not ns.date is None:
        date = ns.date

pause_between_days = 60
days_since_last_expiry = 0

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
        if (e.retry_after_secs > 1200):
            # API Limit goes by the hour, so refresh the client after 10 minutes to
            # make sure that it doesn't expire
            time.sleep(600)
            logmsg('refreshing client tokens')
            authd_client.client.refresh_token()

            # wait the rest of the time
            time.sleep(e.retry_after_secs - 600)
        else:
            time.sleep(e.retry_after_secs + 10)
    except HTTPUnauthorized as e:
        logmsg('token has expired, exiting. start with new date: {}'.format(date))
        sys.exit(1)
    else:
        days_since_last_expiry += 1
        date -= datetime.timedelta(days=1)
        if not r:
            break
        # wait a minute just to not throttle the API since we can only do 150
        # calls per hour
        time.sleep(pause_between_days)

# Always redump the last dumped day because we may have dumped it before the day was finished.
dump_day(authd_client, date)
