import logging
from datetime import datetime, timedelta
import os
from fetcher.services.github_service import GithubService


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _get_environment_variables() -> str:

    github_token = os.getenv("GH_TOKEN")
    if not github_token:
        raise ValueError(
            "The env variable GH_TOKEN is empty or missing")

    return github_token


def fetch_usage_report_daily():

    github_token = _get_environment_variables()
    github_service = GithubService(github_token)
    yesterday = (datetime.today() - timedelta(days=1)).day
    daily_usage_report_json = github_service.get_current_daily_usage_for_enterprise(day=yesterday)

    '''Code for uploading results to the DB needs to be added here.'''


if __name__ == "__main__":
    fetch_usage_report_daily()
