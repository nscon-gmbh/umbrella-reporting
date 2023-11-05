import argparse
import json
import time
import requests
from requests.auth import HTTPBasicAuth
from beautifultable import BeautifulTable
from decouple import config

# Konfiguration und Umgebungsvariablen
TOKEN_URL = config("TOKEN_URL", default="https://api.umbrella.com/auth/v2/token")
REPORT_URL = config("REPORT_URL", default="https://api.umbrella.com/reports/v2")
CLIENT_ID = config('API_KEY')
CLIENT_SECRET = config('API_SECRET')

# Authentifizierungsklasse
class OAuth2Authenticator:
    def __init__(self, token_url, client_id, client_secret):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def authenticate(self):
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        response = requests.post(self.token_url, auth=auth)
        response.raise_for_status()
        self.token = response.json()
        return self.token

# API-Client-Klasse
class UmbrellaAPIClient:
    def __init__(self, authenticator, base_url):
        self.authenticator = authenticator
        self.base_url = base_url

    def query(self, endpoint):
        if not self.authenticator.token:
            self.authenticator.authenticate()
        headers = {'Authorization': f"Bearer {self.authenticator.token['access_token']}"}
        response = requests.get(f"{self.base_url}/{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()

# Datum-Validierungsfunktion
def check_date(value):
    valid_words = ["days", "weeks", "minutes", "now", "seconds"]
    if any(word in value for word in valid_words):
        return value
    if int(time.time()) - int(value) >= 0:
        return value
    return None

# Hauptfunktion
def main():
    # Argument-Parser-Setup
    parser = argparse.ArgumentParser(description="Query the Umbrella API for deployment status.")
    parser.add_argument(
        "-f", "--from_date",
        help="A timestamp or relative time string (e.g., '-1days'). Filter for data after this time.",
        required=True,
        type=check_date
    )
    parser.add_argument(
        "-t", "--to_date",
        help="A timestamp or relative time string (e.g., 'now'). Filter for data before this time, default is 'now'.",
        default="now",
        type=check_date
    )
    args = parser.parse_args()

    # Erstellen der Authentifizierungs- und API-Client-Instanzen
    authenticator = OAuth2Authenticator(TOKEN_URL, CLIENT_ID, CLIENT_SECRET)
    api_client = UmbrellaAPIClient(authenticator, REPORT_URL)

    # API-Abfrage
    params = f"from={args.from_date}&to={args.to_date}&limit=10&offset=0"
    endpoint = f"deployment-status?{params}"
    response = api_client.query(endpoint)

    # Datenpräsentation
    status_table = BeautifulTable()
    for item in response["data"]:
        status_table.rows.append([item["type"]["label"], item["activecount"], item["count"]])
    status_table.columns.header = ["Label", "Active", "Count"]
    status_table.set_style(BeautifulTable.STYLE_MARKDOWN)
    print(f"Deployment Status between {args.from_date} and {args.to_date}")
    print(status_table)

if __name__ == "__main__":
    main()

