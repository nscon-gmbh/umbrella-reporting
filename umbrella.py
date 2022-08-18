import requests
import json
from decouple import config
from beautifultable import BeautifulTable
import argparse
import time

# read config items from .env-file in the same folder
token_url = config("TOKEN_URL", default="https://management.api.umbrella.com/auth/v2/oauth2/token")
org_id = config("ORG_ID")
report_url = config("REPORT_URL", default="https://reports.api.umbrella.com/v2")
# BASIC_TOKEN can be created with 
# echo 'your_api_key:your_api_secret' | base64 >> .env
base64_string= config('BASIC_TOKEN')

payload = {}
headers = {}
device_status = []

def check_date(value):
    '''Checks if the given date contains either "days","weeks", "minutes", "now" (relative date) or is a timestamp in the past (or now)'''

    valid_words = ["days", "weeks", "minutes", "now", "seconds"]
    res = [i for i in valid_words if(i in value)]
    if bool(res) == True:
        return value
    elif int(time.time_ns() / 1000) - int(value) >= 0:
        return value
    else:
        return value

# from-date/to-date as arguments
parser=argparse.ArgumentParser()
parser.add_argument("-f", "--from_date", help="A timestamp or relative time string (for example: '-1days').  Filter for data that appears after this time", required=True, type=check_date)
parser.add_argument("-t", "--to_date", help="A timestamp or relative time string (for example: 'now').  Filter for data that appears before this time, default is 'now'.", default="now")
args=parser.parse_args()
from_date=args.from_date
to_date=args.to_date

headers = {
    "Authorization": f"Basic {base64_string}"
}

# get Authorization token 

try:
    token = requests.request("GET", token_url, headers=headers, data=payload)
    token.raise_for_status()
except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

token = json.loads(token.text)["access_token"]
headers["Authorization"] = f"Bearer {token}"

params=f"from={from_date}&to={to_date}&limit=10&offset=0"

try:
    req = requests.get(report_url + f"organizations/{org_id}/deployment-status?{params}", headers=headers, data=payload)
    req.raise_for_status()
except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

response = json.loads(req.text)

# create table with rows from response data
status_table = BeautifulTable()

for i in response["data"]:
    status_table.rows.append([i["type"]["label"],i["activecount"],i["count"]])

# define header, table style
status_table.columns.header = ["Label", "Active", "Count"]
status_table.set_style(BeautifulTable.STYLE_MARKDOWN)

#print table
print(f"Deployment-Status between {from_date} and {to_date}")
print(status_table)

