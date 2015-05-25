#!/usr/bin/env python
import pprint
import sys
import os

import interface 

#add the ./python-* folders to paths for ease of importing modules
dirLoc = os.path.dirname(os.path.realpath(__file__))
fitbitDir = dirLoc + '/python-fitbit/'
sys.path.append(fitbitDir)
from fitbit.api import FitbitOauth2Client 


if __name__ == '__main__':

    client_id = sys.argv[1]
    client_sec = sys.argv[2]

    # setup
    pp = pprint.PrettyPrinter(indent=4)
    print('** OAuth Python GET KEYS **\n')
    client = FitbitOauth2Client(client.key, client.secret)

    ## get request token
    #print('* Obtain a request token ...\n')
    #token = client.fetch_request_token()
    #print('RESPONSE')
    #pp.pprint(token)
    #print('')

    #print('* Authorize the request token in your browser\n')
    #print(client.authorize_token_url())
    #try:
        #verifier = raw_input('Verifier: ')
    #except NameError:
        ## Python 3.x
        #verifier = input('Verifier: ')

    ## get access token
    #print('\n* Obtain an access token ...\n')
    #token = client.fetch_access_token(verifier)
    #print('RESPONSE')
    #pp.pprint(token)
    #print('')
    #return(token)




        
   
