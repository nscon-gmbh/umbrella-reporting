"""umbrella.py - get deployment status for a given time range.
takes from and to as arguments (time range)
"""
import argparse
import json
import time

import requests
from beautifultable import BeautifulTable
from decouple import config

# read config items from .env-file in the same folder
TOKEN_URL = config(
    "TOKEN_URL",
    default="https://management.api.umbrella.com/auth/v2/oauth2/token",
)
ORG_ID = config("ORG_ID")
REPORT_URL = config("REPORT_URL", default="https://reports.api.umbrella.com/v2")
# BASIC_TOKEN can be created with
# echo 'your_api_key:your_api_secret' | base64 >> .env
BASE64_STRING = config("BASIC_TOKEN")

payload = {}
headers = {}
device_status = []


def check_date(value):
    """Checks if the given date contains either "days","weeks", "minutes",
    "now" (relative date) or is a timestamp in the past (or now)
    """

    valid_words = ["days", "weeks", "minutes", "now", "seconds"]
    res = [i for i in valid_words if i in value]
    if bool(res) is True:
        return value
    if int(time.time_ns() / 1000) - int(value) >= 0:
        return value
    return None


# from-date/to-date as arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--from_date",
    help="A timestamp or relative time string (for example: '-1days').\
    Filter for data that appears after this time",
    required=True,
    type=check_date,
)
parser.add_argument(
    "-t",
    "--to_date",
    help="A timestamp or relative time string (for example: 'now').\
    Filter for data that appears before this time, default is 'now'.",
    default="now",
)
args = parser.parse_args()
from_date = args.from_date
to_date = args.to_date

headers = {"Authorization": f"Basic {BASE64_STRING}"}

# get Authorization token

try:
    token = requests.request(
        "GET", TOKEN_URL, headers=headers, data=payload, timeout=23
    )
    token.raise_for_status()
except requests.exceptions.HTTPError as err:
    raise SystemExit(err) from err

token = json.loads(token.text)["access_token"]
headers["Authorization"] = f"Bearer {token}"

params = f"from={from_date}&to={to_date}&limit=10&offset=0"

try:
    req = requests.get(
        REPORT_URL + f"organizations/{ORG_ID}/deployment-status?{params}",
        headers=headers,
        data=payload,
        timeout=23,
    )
    req.raise_for_status()
except requests.exceptions.HTTPError as err:
    raise SystemExit(err) from err

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
