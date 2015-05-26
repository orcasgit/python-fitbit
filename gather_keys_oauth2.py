#!/usr/bin/env python
import pprint
import sys
import os

from fitbit.api import FitbitOauth2Client 


def gather_keys(client_id,client_secret, redirect_uri): 
    
    # setup
    pp = pprint.PrettyPrinter(indent=4)
    client = FitbitOauth2Client(client_id, client_secret)

    #get authorization url
    url = client.authorize_token_url(redirect_uri=redirect_uri)

    print('* Authorize the request token in your browser\nCopy code here\n')
    print(url)
    try:
        verifier = raw_input('Code: ')
    except NameError:
        # Python 3.x
        verifier = input('Code: ')

    # get access token
    print('\n* Obtain an access token ...\n')
    token = client.fetch_access_token(verifier,redirect_uri)
    print('RESPONSE')
    pp.pprint(token)
    print('')
    return(token)


if __name__ == '__main__':

    if not (len(sys.argv) == 4):
        print "Arguments: client_id, client_secret, and redirect_uri"
        sys.exit(1)

    client_id = sys.argv[1]
    client_sec = sys.argv[2]
    redirect_uri = sys.argv[3]

    token = gather_keys(client_id,client_sec,redirect_uri)
