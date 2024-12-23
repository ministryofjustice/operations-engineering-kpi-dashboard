import os
import re
from typing import Any, Optional, Tuple
import github
from datetime import datetime, timezone, timedelta
import concurrent.futures
from fetcher.services.github_service import GithubService
import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _get_environment_variables() -> str:
    github_app_moj_token = os.getenv("GH_APP_MOJ_TOKEN")
    if not github_app_moj_token:
        raise ValueError(
            "The env variable GH_APP_MOJ_TOKEN is empty or missing")
    github_app_ap_token = os.getenv("GH_APP_AS_TOKEN")
    if not github_app_ap_token:
        raise ValueError(
            "The env variable GH_APP_AS_TOKEN is empty or missing")

    return github_app_moj_token, github_app_ap_token


def _calculate_gha_run_minutes_and_cost(run_id: int, repo_object: github.Repository,
                                       github_service: GithubService, os_multipliers: dict[str, int],
                                       minute_cost_usd: float) -> Tuple[float, float]:

    total_minutes = 0.0
    cost_per_run = 0.0
    response = github_service.get_workflow_run_details(repo_name=repo_object.full_name,
                                                       run_id=run_id)

    for os_type, multiplier in os_multipliers.items():
        billable_data = response["billable"].get(os_type)
        if billable_data:
            total_ms = billable_data['total_ms']
            total_minutes += total_ms / 60000
            cost_per_run += total_minutes * minute_cost_usd * multiplier

    return total_minutes, cost_per_run


def _calculcate_gha_repo_minutes_and_cost(repo_object: github.Repository, start_date: str, end_date: str,
                                 github_service: GithubService, os_multipliers: dict[str, int],
                                 minute_cost_usd: float) -> Tuple[float, float]:

    total_minutes_repo = 0.0
    cost_repo = 0.0
    repo_workflow_runs = github_service.get_workflow_runs_for_repo(repo=repo_object,
                                                                   created=f"{start_date}..{end_date}")

    for run in repo_workflow_runs:
        total_minutes_run, cost_for_run = _calculate_gha_run_minutes_and_cost(run.id, repo_object,
                                                                             github_service, os_multipliers, minute_cost_usd)
        if total_minutes_run > 0: 
            total_minutes_repo = total_minutes_repo + total_minutes_run
            cost_repo = round((cost_repo + cost_for_run), 3)

    return total_minutes_repo, cost_repo


def _process_repository(repo_object: github.Repository, start_date: str, end_date: str,
                       github_service: GithubService, os_multipliers: dict[str, int],
                       minute_cost_usd: float) -> Optional[dict]:
    

    workflows = github_service.get_workflows_for_repo(repo=repo_object)
    if workflows.totalCount > 0:
        total_minutes_repo, cost_repo = _calculcate_gha_repo_minutes_and_cost(
            repo_object, start_date, end_date,
            github_service, os_multipliers, minute_cost_usd)

        if cost_repo > 0:
            return {
                "date": end_date,
                "repo_name": repo_object.name,
                "gha_minutes_usage_min": total_minutes_repo,
                "gha_minutes_cost_usd": cost_repo,
                "organization": repo_object.owner.login
            }

    return None


def _run_thread_pool_processing(repo_obj_list: list, start_date: str, end_date: str,
                               github_service: GithubService, os_multipliers: dict[str, int],
                               minute_cost_usd: float) -> list[dict[str, Any]]:

    results = []
    # default value max_workers=min(32, os.cpu_count() + 4)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for repo_object in repo_obj_list:
            futures.append(executor.submit(_process_repository, repo_object, start_date, end_date,
                                           github_service, os_multipliers, minute_cost_usd))

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                results.append(future.result())
                logger.info("Repository gha usage added: %s ", future.result())

    return results


def fetch_gha_usage_data(minute_cost_usd: float = 0.008,
                         period_days: int = 7,
                         os_multipliers: dict = {
                             "UBUNTU": 1,
                             "MACOS": 10,
                             "WINDOWS": 2,
                             }) -> list[dict[str, Any]]:

    results = []
    github_app_moj_token, github_app_ap_token = _get_environment_variables()
    start_date = (datetime.now(timezone.utc) - timedelta(days=period_days)).date().strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = datetime.now(timezone.utc).date().strftime("%Y-%m-%dT%H:%M:%SZ")
    gh_orgs = ["ministryofjustice", "moj-analytical-services"]

    for org_name in gh_orgs:
        if org_name == "ministryofjustice":
            github_service = GithubService(github_app_moj_token, org_name)
        elif org_name == "moj-analytical-services":
            github_service = GithubService(github_app_ap_token, org_name)

        repo_obj_private_list = github_service.get_all_private_non_archived_repos()
        repo_internal_list = github_service.get_all_internal_non_archived_repos()
        repo_obj_list = repo_obj_private_list + repo_internal_list

        results_processing = _run_thread_pool_processing(repo_obj_list, start_date, end_date, github_service, os_multipliers, minute_cost_usd)
        results.extend(results_processing)

    '''Code for uploading results to the DB needs to be added here.'''


if __name__ == "__main__":
    fetch_gha_usage_data()
