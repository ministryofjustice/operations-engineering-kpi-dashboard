import logging
import json
from calendar import timegm
from time import gmtime, sleep
from typing import Callable, Any
from requests import Session
import github
from github import (Github, RateLimitExceededException)
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportServerError
from retrying import retry


logging.basicConfig(level=logging.INFO)


def retries_github_rate_limit_exception_at_next_reset_once(func: Callable) -> Callable:
    def decorator(*args, **kwargs):
        """
        A decorator to retry the method when rate limiting for GitHub resets if the method fails due to Rate Limit related exception.

        WARNING: Since this decorator retries methods, ensure that the method being decorated is idempotent
         or contains only one non-idempotent method at the end of a call chain to GitHub.

         Example of idempotent methods are:
            - Retrieving data
         Example of (potentially) non-idempotent methods are:
            - Deleting data
            - Updating data
        """
        try:
            return func(*args, **kwargs)
        except (RateLimitExceededException, TransportServerError) as exception:
            logging.warning(
                f"Caught {type(exception).__name__}, retrying calls when rate limit resets.")
            rate_limits = args[0].github_client_core_api.get_rate_limit()
            rate_limit_to_use = rate_limits.core if isinstance(
                exception, RateLimitExceededException) else rate_limits.graphql

            reset_timestamp = timegm(rate_limit_to_use.reset.timetuple())
            now_timestamp = timegm(gmtime())
            time_until_core_api_rate_limit_resets = (
                reset_timestamp - now_timestamp) if reset_timestamp > now_timestamp else 0

            wait_time_buffer = 5
            sleep(time_until_core_api_rate_limit_resets +
                  wait_time_buffer if time_until_core_api_rate_limit_resets else 0)
            return func(*args, **kwargs)

    return decorator


class GithubService:
    def __init__(
        self,
        org_token: str,
        org_name: str,
    ) -> None:
        self.github_client_core_api = Github(org_token)
        self.org_name = org_name
        self.github_client_gql_api: Client = Client(transport=AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {org_token}"},
        ), execute_timeout=120)
        self.github_client_rest_api = Session()
        self.github_client_rest_api.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {org_token}",
            }
        )
        
    def repo_is_non_archived_private(self, repo):
        if not repo.archived and repo.visibility == "private":
            return repo
        return None


    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    @retries_github_rate_limit_exception_at_next_reset_once
    def get_all_private_non_archived_repos(self) -> list[github.Repository]:
        
        non_archived_private_repos=[]
        org = self.github_client_core_api.get_organization(self.org_name)
        non_archived_private_repos = [repo for repo in org.get_repos(type="private") if (not repo.archived)]
        
        return non_archived_private_repos

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    @retries_github_rate_limit_exception_at_next_reset_once
    def get_all_internal_non_archived_repos(self) -> list[github.Repository]:

        org = self.github_client_core_api.get_organization(self.org_name)
        non_archived_internal_repos = [repo for repo in org.get_repos() if (not repo.archived and repo.visibility == "internal")]

        return non_archived_internal_repos
    
    def get_all_repos(self) -> list[github.Repository]:

        org = self.github_client_core_api.get_organization(self.org_name)
        repos_all = org.get_repos() 

        return repos_all

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    @retries_github_rate_limit_exception_at_next_reset_once
    def get_workflows_per_repo(self, repo: github.Repository) -> github.PaginatedList:

        workflows = repo.get_workflows()

        return workflows

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    @retries_github_rate_limit_exception_at_next_reset_once
    def get_workflow_runs(self, workflow: github.Workflow) -> github.PaginatedList: 

        workflow_runs = workflow.get_runs()

        return workflow_runs

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    @retries_github_rate_limit_exception_at_next_reset_once
    def get_workflow_runs_per_repo(self, repo: github.Repository, created: str) -> github.PaginatedList: 

        repo_workflow_runs = repo.get_workflow_runs(created=created)

        return repo_workflow_runs

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    @retries_github_rate_limit_exception_at_next_reset_once
    def get_workflow_run_details(self, repo_name: str, run_id: int) -> Any:
        response_okay = 200
        url = f"https://api.github.com/repos/{repo_name}/actions/runs/{run_id}/timing"

        response = self.github_client_rest_api.get(url, timeout=10)
        if response.status_code == response_okay:
            return json.loads(response.content.decode("utf-8"))
        raise ValueError(
            f"Failed to get details for {run_id} in repository {repo_name}. Response status code: {response.status_code}")