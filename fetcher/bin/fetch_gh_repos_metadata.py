import logging
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


def fetch_gh_repos_metadata():

    github_token = _get_environment_variables()
    github_service = GithubService(github_token)

    organisations = github_service.get_all_organisations_in_enterprise()
    for org in organisations:
        repos = github_service.get_non_archived_repos(org_name=org)
        for repo in repos:
            KpiService(os.getenv("KPI_DASHBOARD_URL"), os.getenv("KPI_DASHBOARD_API_KEY")).post_github_repository_metadata(
                repo.id, repo.name, repo.full_name, repo.owner.login, repo.visibility)

        logger.info("Repository metadata fetched for the org: %s ", org)


if __name__ == "__main__":
    fetch_gh_repos_metadata()
