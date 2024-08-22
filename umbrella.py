"""
This script interacts with the Umbrella API to retrieve and display reports for deployment status
and security activity. It supports OAuth2 authentication and accepts command-line arguments to
define the date range for data retrieval. Results are displayed in a tabular format.

Usage:
    python script.py --report_type <type> --from_date <start_date> --to_date <end_date>

Where <report_type> can be 'deployment' or 'activity' and <start_date> and <end_date> can be timestamps 
or relative times like '-1days'.
"""

import argparse
import time
import logging
from collections import defaultdict
import requests
from beautifultable import BeautifulTable
from decouple import config as decouple_config
from requests.auth import HTTPBasicAuth
from requests.exceptions import (
    HTTPError,
    ConnectionError as RequestsConnectionError,
    Timeout,
    RequestException,
)

# Set up logging based on environment variable
log_level = decouple_config("LOG_LEVEL", default="INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)


class Config:  # pylint: disable=R0903
    """Handles configuration using decouple for environment variables."""

    def __init__(self):
        self.token_url = decouple_config(
            "TOKEN_URL", default="https://api.umbrella.com/auth/v2/token"
        )
        self.report_url = decouple_config(
            "REPORT_URL", default="https://api.umbrella.com/reports/v2"
        )
        self.categories_url = decouple_config(
            "CATEGORIES_URL", default="https://api.umbrella.com/reports/v2/categories"
        )
        self.client_id = decouple_config("API_KEY")
        self.client_secret = decouple_config("API_SECRET")


class OAuth2Authenticator:  # pylint: disable=R0903
    """Handles OAuth2 authentication to retrieve an access token."""

    def __init__(self, config):
        """Initializes the authenticator with the given configuration."""
        self.token_url = config.token_url
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.token = None

    def authenticate(self):
        """Authenticates with the OAuth2 endpoint and sets the access token.

        Returns:
            dict: The retrieved OAuth2 access token.
        """
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        try:
            response = requests.post(self.token_url, auth=auth, timeout=10)
            response.raise_for_status()
            self.token = response.json()
            logger.info("Authentication successful.")
            return self.token
        except (HTTPError, RequestsConnectionError, Timeout, RequestException) as err:
            logger.error("Error during authentication: %s", err)
            raise

class UmbrellaAPIClient:  # pylint: disable=R0903
    """API client for the Umbrella service that handles making requests."""

    def __init__(self, authenticator, base_url):
        """Initializes the API client with an authenticator and base URL."""
        self.authenticator = authenticator
        self.base_url = base_url

    def query(self, endpoint):
        """Queries the API at the specified endpoint and returns the response data."""
        if not self.authenticator.token:
            self.authenticator.authenticate()
        headers = {
            "Authorization": f"Bearer {self.authenticator.token['access_token']}"
        }
        logger.info(
            "Requesting data from API endpoint: %s", f"{self.base_url}/{endpoint}"
        )
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}", headers=headers, timeout=10
            )
            response.raise_for_status()
            logger.info("API query successful.")
            return response.json()
        except HTTPError as http_err:
            if response.status_code == 429:
                logger.warning(
                    "Rate limit exceeded. Status code: 429. Retrying after backoff."
                )
                time.sleep(60)  # Exponential backoff could be used here
                return self.query(endpoint)  # Recursive retry
            if response.status_code in [503, 504]:
                logger.warning(
                    "Service unavailable. Status code: %s. Retrying...",
                    response.status_code,
                )
                time.sleep(30)  # Backoff for service unavailability
                return self.query(endpoint)  # Recursive retry

            logger.error("HTTP error occurred: %s", http_err)
            raise
        except (RequestsConnectionError, Timeout) as conn_err:
            logger.error("Network error occurred: %s", conn_err)
            raise
        except RequestException as req_err:
            logger.error("Request error occurred: %s", req_err)
            raise


def get_security_category_ids(api_client):
    """Retrieves all category IDs that are security-relevant."""
    categories_data = api_client.query("categories")
    category_map = {}
    for category in categories_data.get("data", []):
        if category["type"] == "security":
            category_map[category["label"]] = category["id"]
    return category_map


def is_relative_date(value):
    """Checks if the given value is a relative date."""
    valid_words = ["days", "weeks", "minutes", "now", "seconds"]
    return any(word in value for word in valid_words)


def check_date(value):
    """Validates the date value to ensure it's either a relative time string or a past timestamp."""
    if is_relative_date(value):
        return value
    try:
        if int(time.time()) - int(value) >= 0:
            return value
    except ValueError:
        logger.error("Invalid date value: %s", value)
    return None


def validate_dates(from_date, to_date):
    """Validates that both dates are either relative or both are timestamps."""
    if is_relative_date(from_date) != is_relative_date(to_date):
        raise ValueError(
            "Both from_date and to_date must be either relative dates or timestamps. "
            "Mixing is not allowed."
        )
    return True


class DataPresenter:  # pylint: disable=R0903
    """Handles the presentation of data in various formats."""

    def __init__(self, data):
        """Initializes the DataPresenter with the data to present."""
        self.data = data

    def present_as_table(self, report_type):
        """Presents the data as a table using BeautifulTable."""
        status_table = BeautifulTable()
        if report_type == "deployment":
            for item in self.data:
                status_table.rows.append(
                    [item["type"]["label"], item["activecount"], item["count"]]
                )
            status_table.columns.header = ["Label", "Active", "Count"]
        elif report_type == "activity":
            identity_domain_map = defaultdict(lambda: defaultdict(int))
            identity_category_map = defaultdict(lambda: defaultdict(set))
            last_seen_map = defaultdict(lambda: defaultdict(str))

            for item in self.data:
                identity = item.get("identities", [{"label": "Unknown"}])[0]["label"]
                domain = item.get("domain", "N/A")
                category = item.get("policycategories", [{"label": "N/A"}])[0]["label"]
                last_seen = item.get("date", "N/A")

                identity_domain_map[identity][domain] += 1
                identity_category_map[identity][domain].add(category)
                if last_seen_map[identity][domain] < last_seen:
                    last_seen_map[identity][domain] = last_seen

            for identity, domains in identity_domain_map.items():
                for domain, count in domains.items():
                    categories = ", ".join(identity_category_map[identity][domain])
                    last_seen = last_seen_map[identity][domain]
                    status_table.rows.append(
                        [identity, domain, count, categories, last_seen]
                    )

            status_table.columns.header = [
                "Identity",
                "Domain",
                "Count",
                "Category",
                "Last Seen",
            ]
        return status_table


def validate_verdict(verdict):
    """Validates that the verdict contains only allowed values."""
    valid_verdicts = {"allowed", "blocked", "proxied"}

    if verdict:
        # Split the input by commas and trim whitespace
        verdicts = {v.strip().lower() for v in verdict.split(",")}

        # Check if all provided verdicts are in the set of valid verdicts
        if not verdicts.issubset(valid_verdicts):
            raise ValueError(
                f"Invalid verdict value(s) provided: {verdict}. "
                f"Allowed values are: {', '.join(valid_verdicts)}"
            )
    return verdict


def main():
    """Main function that orchestrates the authentication, querying, and presentation of data."""
    parser = argparse.ArgumentParser(
        description="Query the Umbrella API for deployment and activity reports."
    )
    parser.add_argument(
        "-r",
        "--report_type",
        help="Type of report to retrieve: 'deployment' or 'activity'.",
        required=True,
        choices=["deployment", "activity"],
    )
    parser.add_argument(
        "-f",
        "--from_date",
        help="A timestamp or relative time string (e.g., '-1days'). Filter for data after this time.",
        required=True,
        type=check_date,
    )
    parser.add_argument(
        "-t",
        "--to_date",
        help=(
            "A timestamp or relative time string (e.g., 'now'). Filter for data before this time, "
            "default is 'now'."
        ),
        default="now",
        type=check_date,
    )
    parser.add_argument(
        "--verdict",
        help="A verdict string to filter activity report (e.g., 'allowed,blocked,proxied').",
        default=None,
        required=False,
        type=validate_verdict,
    )
    args = parser.parse_args()

    # Validate that from_date and to_date are consistent
    validate_dates(args.from_date, args.to_date)

    # Load configuration
    config = Config()

    authenticator = OAuth2Authenticator(config)
    api_client = UmbrellaAPIClient(authenticator, config.report_url)

    # Retrieve security-relevant category IDs for filtering
    category_ids = get_security_category_ids(api_client)
    category_filter = ",".join(str(id) for id in category_ids.values())

    offset = 0
    limit = 100
    all_data = []
    endpoint = None

    while True:
        if args.report_type == "deployment":
            params = (
                f"from={args.from_date}&to={args.to_date}&limit={limit}&offset={offset}"
            )
            endpoint = f"deployment-status?{params}"
        elif args.report_type == "activity":
            params = (
                f"from={args.from_date}&to={args.to_date}&limit={limit}&offset={offset}"
            )
            if args.verdict:
                params += f"&verdict={args.verdict}"
            params += f"&categories={category_filter}"
            endpoint = f"activity?{params}"

        if endpoint is None:
            logger.error("No endpoint defined. Exiting.")
            return

        logger.info("Final API request URL: %s", f"{api_client.base_url}/{endpoint}")
        response = api_client.query(endpoint)
        data = response.get("data", [])
        all_data.extend(data)

        # Check if the number of results matches the limit
        if len(data) < limit:
            break  # If less than the limit, assume no more data is available
        offset += limit  # Increment offset to get the next set of results

    presenter = DataPresenter(all_data)
    status_table = presenter.present_as_table(args.report_type)
    print(
        f"{args.report_type.capitalize()} Report between "
        f"{args.from_date} and {args.to_date}"
    )
    print(status_table)


if __name__ == "__main__":
    main()
