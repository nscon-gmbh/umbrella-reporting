# Prerequisites
# pip install requests
# pip install requests requests_oauthlib
import requests
import json
import os
import time
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2 import TokenExpiredError
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
from decouple import config

token_url = config('TOKEN_URL', default='https://management.api.umbrella.com/auth/v2/oauth2/token')
# Export/Set the environment variables
client_id = config('API_KEY') 
client_secret = config('API_SECRET')

class UmbrellaAPI:
    def __init__(self, url, ident, secret):
        self.url = url
        self.ident = ident
        self.secret = secret
        self.token = None

    def GetToken(self):
        auth = HTTPBasicAuth(self.ident, self.secret)
        client = BackendApplicationClient(client_id=self.ident)
        oauth = OAuth2Session(client=client)
        self.token = oauth.fetch_token(token_url=self.url, auth=auth)
        return self.token

# Exit out if the client_id, client_secret are not set.
for var in ['API_SECRET', 'API_KEY']:
    if os.environ.get(var) == None:
        print("Required environment variable: {} not set".format(var))
        exit()

# Get token and make an API request
api = UmbrellaAPI(token_url, client_id, client_secret)
print("Token: " + str(api.GetToken()))
