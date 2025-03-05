import logging
import json
from datetime import datetime, timedelta
import os
from fetcher.services.github_service import GithubService
from fetcher.services.kpi_service import KpiService


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
    yesterday_date = (datetime.today() - timedelta(days=1)).date()
    report_usage_data = github_service.get_current_daily_usage_for_enterprise(month=yesterday_date.month, day=yesterday_date.day)

    KpiService(os.getenv("KPI_DASHBOARD_URL"), os.getenv("KPI_DASHBOARD_API_KEY")).track_github_usage_report_daily(str(yesterday_date), json.dumps(report_usage_data))


if __name__ == "__main__":
    fetch_usage_report_daily()
