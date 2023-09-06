"""get deployment status for a given time range.
takes from and to as arguments (time range)
"""
import argparse
import json
import time
import requests
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2 import TokenExpiredError
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
from beautifultable import BeautifulTable
from decouple import config

# read config items from .env-file in the same folder
TOKEN_URL = config(
    "TOKEN_URL",
    default="https://api.umbrella.com/auth/v2/token",
)
ORG_ID = config("ORG_ID")
REPORT_URL = config("REPORT_URL", default="https://api.umbrella.com/reports/v2")

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

    def Query(self, end_point):
        success = False
        req = None
        if self.token == None:
            self.GetToken()
        while not success:
            try:
                api_headers = {'Authorization': "Bearer " + self.token['access_token']}
                req = requests.get('https://api.umbrella.com/reports/v2/{}'.format(end_point), headers=api_headers)
                req.raise_for_status()
                success = True
            except TokenExpiredError:
                token = self.GetToken()
            except Exception as e:
                raise(e)
        return req

# Get token
api = UmbrellaAPI(TOKEN_URL, client_id, client_secret)


device_status = []

def check_date(value):
    """Checks if date is valid.

    Checks if the given date contains either "days","weeks", "minutes",
    "now" (relative date) or is a timestamp in the past (or now)

    Args:
      value (str): date as string

    Returns:
       value or None: depends on the check


    """

    # review code
    valid_words = ["days", "weeks", "minutes", "now", "seconds"]
    res = [i for i in valid_words if i in value]
    if bool(res) is True:
        return value
    if int(time.time_ns() / 1000) - int(value) >= 0:
        return value
    return None


if __name__ == "__main__":
    # from-date/to-date as arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--from_date",
        help=(
            "A timestamp or relative time string (for example: '-1days').        Filter"
            " for data that appears after this time"
        ),
        required=True,
        type=check_date,
    )
    parser.add_argument(
        "-t",
        "--to_date",
        help=(
            "A timestamp or relative time string (for example: 'now').        Filter"
            " for data that appears before this time, default is 'now'."
        ),
        default="now",
    )
    args = parser.parse_args()
    from_date = args.from_date
    to_date = args.to_date

    params = f"from={from_date}&to={to_date}&limit=10&offset=0"
    endpoint = f"deployment-status?{params}"

    req = api.Query(endpoint)
    response = json.loads(req.text)

    # create table with rows from response data
    status_table = BeautifulTable()

    for i in response["data"]:
        status_table.rows.append([i["type"]["label"], i["activecount"], i["count"]])

    # define header, table style
    status_table.columns.header = ["Label", "Active", "Count"]
    status_table.set_style(BeautifulTable.STYLE_MARKDOWN)

    # print table
    print(f"Deployment-Status between {from_date} and {to_date}")
    print(status_table)
