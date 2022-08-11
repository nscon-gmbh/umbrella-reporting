# Prerequisites
# pip install requests
# pip install requests requests_oauthlib
import requests
import json
from decouple import config
import pprint

token_url = config('TOKEN_URL', default='https://management.api.umbrella.com/auth/v2/oauth2/token')
org_id = config('ORG_ID')
report_url = "https://reports.api.umbrella.com/v2"
base64_string= config('BASIC_TOKEN')

payload = {}
headers = {}
from_date = "-7days"
to_date = "now"


headers = {
    "Authorization": f"Basic {base64_string}"
}

token = requests.request("GET", token_url, headers=headers, data=payload)
token = json.loads(token.text)["access_token"]

headers["Authorization"] = f"Bearer {token}"

params=f"from={from_date}&to={to_date}&limit=10&offset=0"
req_item="deployment-status"


req = requests.get(report_url + f"organizations/{org_id}/{req_item}?{params}", headers=headers, data=payload)
response = json.loads(req.text)
for i in response['data']:
    print(i['type']['label'], " : ", i['activecount'], "/", i['count'])
