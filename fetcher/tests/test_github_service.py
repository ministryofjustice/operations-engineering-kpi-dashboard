import json
from typing import Optional
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from github.Repository import Repository
from github.Workflow import Workflow
from github.Organization import Organization
from github.PaginatedList import PaginatedList
import pytest
from services.github_service import GithubService


def create_mock_repo(name: str, archived: bool, visibility: Optional[str] = None) -> MagicMock:
    mock_repo = MagicMock(spec=Repository)
    mock_repo.name = name
    mock_repo.archived = archived
    mock_repo.visibility = visibility

    return mock_repo


def create_mock_workflow(id: int, name: str) -> MagicMock:
    mock_workflow = MagicMock(spec=Workflow)
    mock_workflow.id = id
    mock_workflow.name = name

    return mock_workflow


def create_mock_workflow_run(id: int, name: str, status: str ) -> MagicMock:
    mock_workflow_run = MagicMock()
    mock_workflow_run.id = id
    mock_workflow_run.name = name
    mock_workflow_run.status = status

    return mock_workflow_run

@pytest.fixture
def mocks_github_service(mocker):

    mock_github = mocker.patch("services.github_service.Github", autospec=True)
    mock_transport = mocker.patch("services.github_service.AIOHTTPTransport")
    mock_client = mocker.patch("services.github_service.Client")
    mock_session = mocker.patch("services.github_service.Session")
    mock_session_instance = mock_session.return_value
    mock_session_instance.headers = {"Authorization": "Bearer test_token", "Accept": "application/vnd.github+json"}
    gh_service = GithubService(org_token="test_token", org_name="test_org")

    return {
        "gh_service": gh_service,
        "github": mock_github,
        "transport": mock_transport,
        "client": mock_client,
        "session": mock_session
        }


class TestGithubService:

    @pytest.fixture(autouse=True)
    def setup(self, mocks_github_service):
        self.gh_service = mocks_github_service["gh_service"]
        self.github = mocks_github_service["github"]
        self.transport = mocks_github_service["transport"]
        self.client = mocks_github_service["client"]
        self.session = mocks_github_service["session"]

    def test_github_service_init(self):

        assert self.gh_service.org_name == "test_org"
        self.github.assert_called_once_with("test_token")
        self.client.assert_called_once()
        self.transport.assert_called_once()
        self.session.assert_called_once()
        assert self.gh_service.github_client_rest_api.headers["Authorization"] == "Bearer test_token"
        assert self.gh_service.github_client_rest_api.headers["Accept"] == "application/vnd.github+json"
        isinstance(self.gh_service.github_client_core_api, MagicMock)

    def test_get_non_archived_repos(self):

        mock_org = MagicMock(spec=Organization)
        mock_repos_list = [
            create_mock_repo(name="repo1", archived=True),
            create_mock_repo(name="repo2", archived=False),
            create_mock_repo(name="repo3", archived=False)
        ]
        mock_repos = MagicMock(spec=PaginatedList)
        mock_repos.__iter__.return_value = iter(mock_repos_list)
        self.gh_service.github_client_core_api.get_organization.return_value = mock_org
        mock_org.get_repos.return_value = mock_repos
        result_repos = self.gh_service.get_non_archived_repos("ministryofjustice")

        assert len(result_repos) == 2
        assert all(not repo.archived for repo in result_repos)
        assert all(repo.name in ['repo2', 'repo3'] for repo in result_repos)

    def test_get_all_private_non_archived_repos(self):

        mock_org = MagicMock(spec=Organization)
        mock_private_repos_list = [
            create_mock_repo(name="repo1", archived=True),
            create_mock_repo(name="repo2", archived=False),
            create_mock_repo(name="repo3", archived=False)
        ]
        mock_private_repos = MagicMock(spec=PaginatedList)
        mock_private_repos.__iter__.return_value = iter(mock_private_repos_list)
        self.gh_service.github_client_core_api.get_organization.return_value = mock_org
        mock_org.get_repos.return_value = mock_private_repos
        repos = self.gh_service.get_all_private_non_archived_repos()

        assert len(repos) == 2
        assert all(not repo.archived for repo in repos)
        assert all(repo.name in ['repo1', 'repo2', 'repo3'] for repo in repos)

    def test_get_all_internal_non_archived_repos(self):

        mock_org = MagicMock(spec=Organization)
        mock_repo_all_list = [
            create_mock_repo(name="repo1", archived=False, visibility="internal"),
            create_mock_repo(name="repo2", archived=True, visibility="internal"),
            create_mock_repo(name="repo3", archived=False, visibility="public"),
            create_mock_repo(name="repo4", archived=False, visibility="private"),
            create_mock_repo(name="repo5", archived=False, visibility="internal")
        ]
        mock_all_repos = MagicMock(spec=PaginatedList)
        mock_all_repos.__iter__.return_value = iter(mock_repo_all_list)

        self.gh_service.github_client_core_api.get_organization.return_value = mock_org
        mock_org.get_repos.return_value = mock_all_repos
        repos = self.gh_service.get_all_internal_non_archived_repos()

        assert len(repos) == 2
        assert all(not repo.archived for repo in repos)
        assert all(repo.visibility == "internal" for repo in repos)

    def test_get_all_repos(self):

        mock_org = MagicMock(spec=Organization)
        mock_repo_all_list = [
            create_mock_repo(name="repo1", archived=False, visibility="internal"),
            create_mock_repo(name="repo2", archived=True, visibility="internal"),
            create_mock_repo(name="repo3", archived=False, visibility="public"),
            create_mock_repo(name="repo4", archived=False, visibility="private"),
            create_mock_repo(name="repo5", archived=False, visibility="internal")
        ]
        mock_all_repos = MagicMock(spec=PaginatedList)
        mock_all_repos.__iter__.return_value = iter(mock_repo_all_list)
        self.gh_service.github_client_core_api.get_organization.return_value = mock_org
        mock_org.get_repos.return_value = mock_all_repos
        repos = self.gh_service.get_all_repos()

        assert len(list(repos)) == 5
        assert all(repo.name in ['repo1', 'repo2', 'repo3', 'repo4', 'repo5'] for repo in repos)

    def test_get_workflows_for_repo(self):

        mock_repo = MagicMock(spec=Repository)
        mock_workflow_list = [
            create_mock_workflow(id=1, name="workflow1"),
            create_mock_workflow(id=2, name="workflow2"),
            create_mock_workflow(id=3, name="workflow3")
            ]
        mock_workflows = MagicMock(spec=PaginatedList)
        mock_workflows.__iter__.return_value = iter(mock_workflow_list)
        mock_repo.get_workflows.return_value = mock_workflows
        workflows = self.gh_service.get_workflows_for_repo(repo=mock_repo)

        assert len(list(workflows)) == 3
        assert all(workflow.name in ['workflow1', 'workflow2', 'workflow3'] for workflow in workflows)

    def test_get_workflow_runs(self):

        mock_workflow = MagicMock(spec=Workflow)
        mock_workflow_runs_list = [
            create_mock_workflow_run(id=1, name="wf_test_run1", status="completed"), 
            create_mock_workflow_run(id=2, name="wf_test_run2", status="completed"),
            create_mock_workflow_run(id=3, name="wf_test_run3", status="completed")
        ]
        mock_workflow_runs = MagicMock(spec=PaginatedList)
        mock_workflow_runs.__iter__.return_value = iter(mock_workflow_runs_list)
        mock_workflow.get_runs.return_value = mock_workflow_runs
        workflow_runs = self.gh_service.get_workflow_runs(workflow=mock_workflow)

        assert len(list(workflow_runs)) == 3
        assert all(workflow_run.name in ['wf_test_run1', 'wf_test_run2', 'wf_test_run3'] for workflow_run in workflow_runs)

    def test_get_workflow_runs_for_repo(self):

        mock_repo = MagicMock(spec=Repository)
        mock_workflow_runs_repo_list = [
            create_mock_workflow_run(id=1, name="wf_test_run1", status="completed", ), 
            create_mock_workflow_run(id=2, name="wf_test_run2", status="completed"),
            create_mock_workflow_run(id=3, name="wf_test_run3", status="completed")
        ]
        mock_workflow_runs_repo = MagicMock(spec=PaginatedList)
        mock_workflow_runs_repo.__iter__.return_value = iter(mock_workflow_runs_repo_list)
        mock_repo.get_workflow_runs.return_value = mock_workflow_runs_repo
        end_date = datetime.now(timezone.utc).date().strftime("%Y-%m-%dT%H:%M:%SZ")
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).date().strftime("%Y-%m-%dT%H:%M:%SZ")
        created=f"{start_date}..{end_date}"
        workflow_runs_for_repo = self.gh_service.get_workflow_runs_for_repo(repo=mock_repo, created=created)

        assert len(list(workflow_runs_for_repo)) == 3
        assert all(workflow_run.name in ['wf_test_run1', 'wf_test_run2', 'wf_test_run3'] for workflow_run in workflow_runs_for_repo)

    def test_get_workflow_run_details_success(self, mocker):

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({
            "run_duration_ms": 1234567,
            "billable": {
                "UBUNTU": {
                    "total_ms": 123456,
                    "jobs": [
                        {"name": "build", "duration_ms": 654321},
                        {"name": "test", "duration_ms": 234567}
                    ]
                }
            }
        }).encode("utf-8")

        mock_get_request = mocker.patch.object(
            self.gh_service.github_client_rest_api, "get", return_value=mock_response)
        result = self.gh_service.get_workflow_run_details(repo_name="test_repo", run_id=1234)

        assert result == {
            "run_duration_ms": 1234567,
            "billable": {
                "UBUNTU": {
                    "total_ms": 123456,
                    "jobs": [
                        {"name": "build", "duration_ms": 654321},
                        {"name": "test", "duration_ms": 234567}
                    ]
                }
            }
        }

        mock_get_request.assert_called_with(
            "https://api.github.com/repos/test_repo/actions/runs/1234/timing", timeout=10
        )

    def test_get_workflow_run_details_error(self, mocker):

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.content = {"message": "Not Found"}
        mock_get_request = mocker.patch.object(
            self.gh_service.github_client_rest_api, "get", return_value=mock_response)

        with pytest.raises(ValueError) as err:
            self.gh_service.get_workflow_run_details(repo_name="test_repo", run_id=1234)

        assert str(err.value) == (
            "Failed to get details for 1234 in repository test_repo. Response status code: 404"
        )
        mock_get_request.call_count == 3
        mock_get_request.assert_called_with(
            "https://api.github.com/repos/test_repo/actions/runs/1234/timing", timeout=10
        )

    def test_get_current_daily_usage_for_enterprise_success(self, mocker):

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({
            "usageItems": [ {
                "date": "2023-08-01","product": "Actions",
                "sku": "Actions Linux", "quantity": 100,
                "unitType": "minutes", "pricePerUnit": 0.008,
                "grossAmount": 0.8, "discountAmount": 0,
                "netAmount": 0.8, "organizationName": "GitHub",
                "repositoryName": "github/example"
                } ] 
            }).encode("utf-8")

        mock_get_request = mocker.patch.object(
            self.gh_service.github_client_rest_api, "get", return_value=mock_response)
        result = self.gh_service.get_current_daily_usage_for_enterprise(month=1, day=11)

        assert result == {
            "usageItems": [ {
                "date": "2023-08-01","product": "Actions",
                "sku": "Actions Linux", "quantity": 100,
                "unitType": "minutes", "pricePerUnit": 0.008,
                "grossAmount": 0.8, "discountAmount": 0,
                "netAmount": 0.8, "organizationName": "GitHub",
                "repositoryName": "github/example"
                } ] 
            }

        mock_get_request.assert_called_with(
            "https://api.github.com/enterprises/ministry-of-justice-uk/settings/billing/usage?month=1&day=11", timeout=10
        )

    def test_get_current_daily_usage_for_enterprise_error(self, mocker):

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.content = {"message": "Not Found"}
        mock_get_request = mocker.patch.object(
            self.gh_service.github_client_rest_api, "get", return_value=mock_response)

        with pytest.raises(ValueError) as err:
            self.gh_service.get_current_daily_usage_for_enterprise(month=1, day=11)

        assert str(err.value) == (
            "Failed to get usage report for the enterprise ministry-of-justice-uk"
        )
        mock_get_request.call_count == 3
        mock_get_request.assert_called_with(
            "https://api.github.com/enterprises/ministry-of-justice-uk/settings/billing/usage?month=1&day=11", timeout=10
        )
