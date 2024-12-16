import os
import json
from datetime import datetime,timezone, timedelta
import concurrent.futures
from services.github_service import GithubService


def get_environment_variables() -> str:
    github_token = os.getenv("ADMIN_GITHUB_TOKEN")
    if not github_token:
        raise ValueError(
            "The env variable ADMIN_GITHUB_TOKEN is empty or missing")

    return github_token


def calculate_gha_cost_per_run(run_id, repo_object, github_service, os_multipliers, minute_cost_usd):

    total_minutes = 0
    cost_per_run = 0
    response = github_service.get_workflow_run_details(repo_name=repo_object.full_name, run_id=run_id)

    for os_type, multiplier in os_multipliers.items():
        billable_data = response["billable"].get(os_type)
        if billable_data:
            total_ms = billable_data['total_ms']
            total_minutes += total_ms / 60000
            cost_per_run += total_minutes * minute_cost_usd * multiplier

    return total_minutes, cost_per_run


def calculcate_gha_cost_per_repo(repo_object, start_date, end_date, github_service, os_multipliers, minute_cost_usd):

    total_minutes_repo = 0
    cost_repo = 0
    repo_workflow_runs = github_service.get_workflow_runs_repo(repo=repo_object, created=f"{start_date}..{end_date}")

    for run in repo_workflow_runs: 
        total_minutes_run, cost_per_run = calculate_gha_cost_per_run(run.id, repo_object, github_service, os_multipliers, minute_cost_usd)
        if total_minutes_run > 0: 
            total_minutes_repo = total_minutes_repo + total_minutes_run
            cost_repo = round((cost_repo + cost_per_run), 3)

    return total_minutes_repo, cost_repo


def process_repository(repo_object, start_date, end_date, github_service, os_multipliers, minute_cost_usd): 

    workflows = github_service.get_workflows_per_repo(repo=repo_object)
    if workflows.totalCount > 0:
        total_minutes_repo, cost_repo = calculcate_gha_cost_per_repo(
            repo_object, start_date, end_date,
            github_service, os_multipliers, minute_cost_usd)

        if cost_repo > 0:
            return {
                "date": end_date,
                "repo_name": repo_object.name,
                "gha_minutes_usage_min": total_minutes_repo,
                "gha_minutes_cost_usd": cost_repo,
            }

    return None


def main(org_name: str = "ministryofjustice",
                            minute_cost_usd:float = 0.008,
                            os_multipliers = {
                                "UBUNTU": 1,
                                "MACOS": 10,
                                "WINDOWS": 2
                                }
                            ):

    results = []
    github_token = get_environment_variables()
    github_service = GithubService(github_token, org_name)
    start_date = (datetime.now(timezone.utc) - timedelta(days=7)).date().strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = datetime.now(timezone.utc).date().strftime("%Y-%m-%dT%H:%M:%SZ")
    repo_obj_private_list = github_service.get_all_private_non_archived_repos()
    repo_internal_list = github_service.get_all_internal_non_archived_repos()
    repo_obj_list = repo_obj_private_list + repo_internal_list

    # default value max_workers=min(32, os.cpu_count() + 4)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for repo_object in repo_obj_list:
            futures.append(executor.submit(process_repository, repo_object, start_date, end_date, github_service, os_multipliers, minute_cost_usd))
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                results.append(future.result())

    '''# Code for restults validation
    print(results)
    with open("output.json", "w") as json_file:
        json.dump(results, json_file, indent=4)
    
    Code for uploading results to the DB will be added instead 
    '''

if __name__ == "__main__":
    main()