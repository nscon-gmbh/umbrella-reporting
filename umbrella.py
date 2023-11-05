"""
This script interacts with the Umbrella API to retrieve and display deployment status data.
It supports OAuth2 authentication and accepts command-line arguments to define the date range
for the data retrieval. Results are displayed in a tabular format.

Usage:
    python script.py --from_date <start_date> --to_date <end_date>

Where <start_date> and <end_date> can be timestamps or relative times like '-1days'.
"""

import argparse
import time

import requests
from beautifultable import BeautifulTable
from decouple import config
from requests.auth import HTTPBasicAuth

# Configuration and environment variables
TOKEN_URL = config("TOKEN_URL", default="https://api.umbrella.com/auth/v2/token")
REPORT_URL = config("REPORT_URL", default="https://api.umbrella.com/reports/v2")
CLIENT_ID = config('API_KEY')
CLIENT_SECRET = config('API_SECRET')

class OAuth2Authenticator:
    """Handles OAuth2 authentication to retrieve an access token.

    Attributes:
        token_url (str): The URL to retrieve the token from.
        client_id (str): The client ID for OAuth2 authentication.
        client_secret (str): The client secret for OAuth2 authentication.
        token (dict): The retrieved token, initialized as None.
    """

    def __init__(self, token_url, client_id, client_secret):
        """Initializes the authenticator with the given credentials.

        Args:
            token_url (str): The URL to retrieve the token from.
            client_id (str): The client ID for OAuth2 authentication.
            client_secret (str): The client secret for OAuth2 authentication.
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def authenticate(self):
        """Authenticates with the OAuth2 endpoint and sets the access token.

        Returns:
            dict: The retrieved OAuth2 access token.

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails.
        """
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        response = requests.post(self.token_url, auth=auth)
        response.raise_for_status()
        self.token = response.json()
        return self.token

class UmbrellaAPIClient:
    """API client for the Umbrella service that handles making requests.

    Attributes:
        authenticator (OAuth2Authenticator): The authenticator instance to authenticate requests.
        base_url (str): The base URL for the API endpoints.
    """

    def __init__(self, authenticator, base_url):
        """Initializes the API client with an authenticator and base URL.

        Args:
            authenticator (OAuth2Authenticator): The authenticator instance to authenticate requests.
            base_url (str): The base URL for the API endpoints.
        """
        self.authenticator = authenticator
        self.base_url = base_url

    def query(self, endpoint):
        """Queries the API at the specified endpoint and returns the response data.

        Args:
            endpoint (str): The endpoint to query.

        Returns:
            dict: The JSON response from the API.

        Raises:
            requests.exceptions.HTTPError: If the HTTP request fails.
        """
        if not self.authenticator.token:
            self.authenticator.authenticate()
        headers = {'Authorization': f"Bearer {self.authenticator.token['access_token']}"}
        response = requests.get(f"{self.base_url}/{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json()

def check_date(value):
    """Validates the date value to ensure it's either a relative time string or a past timestamp.

    Args:
        value (str): A string representing the date.

    Returns:
        str: The validated date string or None if invalid.
    """
    valid_words = ["days", "weeks", "minutes", "now", "seconds"]
    if any(word in value for word in valid_words):
        return value
    try:
        if int(time.time()) - int(value) >= 0:
            return value
    except ValueError:
        pass
    return None

class DataPresenter:
    """Handles the presentation of data in various formats.

    Attributes:
        data (list): The data to be presented.
    """

    def __init__(self, data):
        """Initializes the DataPresenter with the data to present.

        Args:
            data (list): The data to be presented.
        """
        self.data = data

    def present_as_table(self):
        """Presents the data as a table using BeautifulTable.

        Returns:
            BeautifulTable: A table object with the formatted data.
        """
        status_table = BeautifulTable()
        for item in self.data:
            status_table.rows.append([item["type"]["label"], item["activecount"], item["count"]])
        status_table.columns.header = ["Label", "Active", "Count"]
        status_table.set_style(BeautifulTable.STYLE_MARKDOWN)
        return status_table

def main():
    """Main function that parses command-line arguments and orchestrates the authentication,
    querying, and presentation of data from the Umbrella API.
    """
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

    authenticator = OAuth2Authenticator(TOKEN_URL, CLIENT_ID, CLIENT_SECRET)
    api_client = UmbrellaAPIClient(authenticator, REPORT_URL)

    params = f"from={args.from_date}&to={args.to_date}&limit=10&offset=0"
    endpoint = f"deployment-status?{params}"
    response = api_client.query(endpoint)

    presenter = DataPresenter(response["data"])
    status_table = presenter.present_as_table()
    print(f"Deployment Status between {args.from_date} and {args.to_date}")
    print(status_table)

if __name__ == "__main__":
    main()
