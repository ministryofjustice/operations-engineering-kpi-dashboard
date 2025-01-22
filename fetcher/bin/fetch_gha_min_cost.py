import os
import re
import re
import math
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
    github_app_moj_token = os.getenv("ADMIN_GITHUB_TOKEN")
    if not github_app_moj_token:
        raise ValueError(
            "The env variable GH_APP_MOJ_TOKEN is empty or missing")
    github_app_ap_token = os.getenv("GH_APP_AS_TOKEN")
    if not github_app_ap_token:
        raise ValueError(
            "The env variable GH_APP_AS_TOKEN is empty or missing")

    return github_app_moj_token, github_app_ap_token

def _calculate_job_cost(job, os_multipliers: dict[str, int], minute_cost_usd: float, minutes_per_job: float):
    
    if re.search(r"ubuntu", job.labels[0]):
        multiplier = os_multipliers["UBUNTU"]
    elif re.search(r"windows", job.labels[0]):
        multiplier = os_multipliers["WINDOWS"]
    elif re.search(r"macos", job.labels[0]):
        multiplier = os_multipliers["MACOS"]
    
    cost_per_job = minutes_per_job * multiplier * minute_cost_usd
    
    return cost_per_job

def _calculate_gha_run_minutes_and_cost_v2(jobs: github.PaginatedList, os_multipliers: dict[str, int],
                                           minute_cost_usd: float):
    
    minutes_per_run=0.0
    cost_per_run=0.0
    for job in jobs: 
        if isinstance(job.runner_name, str) and re.search(r"GitHub Actions", job.runner_name): 
            seconds_per_job=(job.completed_at - job.started_at).total_seconds()
            minutes_per_job = math.ceil(seconds_per_job / 60)
            cost_per_job = _calculate_job_cost(job, os_multipliers, minute_cost_usd, minutes_per_job)
            minutes_per_run += minutes_per_job
            cost_per_run += cost_per_job
            
    return minutes_per_run, round(cost_per_run, 3)
            
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
            cost_usd = total_ms / 60000 * minute_cost_usd * multiplier
            total_minutes += total_ms / 60000
            cost_per_run += cost_usd

    return total_minutes, round(cost_per_run, 3)


def _calculcate_gha_repo_minutes_and_cost(repo_object: github.Repository, start_date: str, end_date: str,
                                 github_service: GithubService, os_multipliers: dict[str, int],
                                 minute_cost_usd: float) -> Tuple[float, float]:

    total_minutes_repo = 0.0
    cost_repo = 0.0
    repo_workflow_runs = github_service.get_workflow_runs_for_repo(repo=repo_object,
                                                                   created=f"{start_date}..{end_date}")

    for run in repo_workflow_runs:
        run_jobs=run.jobs()
        minutes_per_run, cost_per_run =_calculate_gha_run_minutes_and_cost_v2(run_jobs, os_multipliers, minute_cost_usd)
        
        if minutes_per_run > 0: 
            total_minutes_repo = total_minutes_repo + minutes_per_run
            cost_repo = cost_repo + cost_per_run
            
    return total_minutes_repo, round(cost_repo, 3)


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
                "start_datetime": start_date,
                "end_datetime": end_date,
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
                         period_days: int = 1,
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
