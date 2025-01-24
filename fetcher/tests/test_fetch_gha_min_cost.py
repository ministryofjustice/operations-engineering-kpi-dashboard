import pytest
from datetime import datetime, timezone
from bin.fetch_gha_min_cost import (
    _get_environment_variables,_calculate_job_cost,
    _calculate_gha_run_minutes_and_cost,
    _calculcate_gha_repo_minutes_and_cost,
    _process_repository, _run_thread_pool_processing,
    fetch_gha_usage_data
)
from unittest.mock import MagicMock, Mock
from github.Repository import Repository


def create_mock_job(name: str, runner_name: str, started_at: datetime, completed_at: datetime) -> MagicMock:
    mock_job = MagicMock()
    mock_job.name = name
    mock_job.runner_name = runner_name
    mock_job.started_at = started_at
    mock_job.completed_at = completed_at

    return mock_job

class TestFetchGithubActionsCost:
    def test_get_environment_variables_success(self, mocker): 

        mocker.patch("os.getenv", side_effect={
            "GH_APP_MOJ_TOKEN": "mock_moj_token",
            "GH_APP_AS_TOKEN": "mock_ap_token"}.get)
        moj_token, ap_token = _get_environment_variables()

        assert moj_token=="mock_moj_token"
        assert ap_token=="mock_ap_token"

    def test_get_environment_variables_moj_token_error(self, mocker): 

        mocker.patch("os.getenv", side_effect={
            "GH_APP_MOJ_TOKEN": None,
            "GH_APP_AS_TOKEN": "mock_ap_token"}.get)

        with pytest.raises(ValueError) as err:
            moj_token, ap_token = _get_environment_variables()

        assert str(err.value) == (
            "The env variable GH_APP_MOJ_TOKEN is empty or missing"
        )
    
    def test_get_environment_variables_ap_token_error(self, mocker): 

        mocker.patch("os.getenv", side_effect={
            "GH_APP_MOJ_TOKEN": "mock_moj_token",
            "GH_APP_AS_TOKEN": None}.get)

        with pytest.raises(ValueError) as err:
            moj_token, ap_token = _get_environment_variables()

        assert str(err.value) == (
            "The env variable GH_APP_AS_TOKEN is empty or missing"
        )
    
    def test_calculate_job_cost_ubuntu(self, mocker):
        
        minute_cost_usd = 0.008
        os_multipliers = {
                             "UBUNTU": 1,
                             "MACOS": 10,
                             "WINDOWS": 2,
                             }
        minutes_for_job = 8.0 
        mock_job = Mock()
        mock_job.labels = ["ubuntu-latest"]
        cost_for_job = _calculate_job_cost(mock_job, os_multipliers, minute_cost_usd, minutes_for_job)
        
        assert cost_for_job == 0.064
    
    
    def test_calculate_job_cost_macos(self, mocker):
        
        minute_cost_usd = 0.008
        os_multipliers = {
                             "UBUNTU": 1,
                             "MACOS": 10,
                             "WINDOWS": 2,
                             }
        minutes_for_job = 8.0 
        mock_job = Mock()
        mock_job.labels = ["macos-latest"]
        cost_for_job = _calculate_job_cost(mock_job, os_multipliers, minute_cost_usd, minutes_for_job)
        
        assert cost_for_job == 0.64


    def test_calculate_gha_run_minutes_and_cost(self, mocker):
        
        minute_cost_usd = 0.008
        os_multipliers = {
                             "UBUNTU": 1,
                             "MACOS": 10,
                             "WINDOWS": 2,
                             }
        mock_jobs=MagicMock()
        mock_job_list = [
            create_mock_job(
                name="job1", runner_name="GitHub Actions 002",
                started_at=datetime(2023, 1, 23, 20, 40, 30, tzinfo=timezone.utc),
                completed_at=datetime(2023, 1, 23, 20, 40, 55, tzinfo=timezone.utc)),
            create_mock_job(
                name="job2", runner_name="GitHub Actions 003",
                started_at=datetime(2023, 1, 23, 20, 40, 59, tzinfo=timezone.utc),
                completed_at=datetime(2023, 1, 23, 20, 42, 55, tzinfo=timezone.utc)),
            create_mock_job(
                name="job3", runner_name="GitHub Actions 003",
                started_at=datetime(2023, 1, 23, 20, 43, 1, tzinfo=timezone.utc),
                completed_at=datetime(2023, 1, 23, 20, 46, tzinfo=timezone.utc))
            ]
        mock_jobs.__iter__.return_value = iter(mock_job_list)
        mock_calculate_job_cost = mocker.patch(
            "bin.fetch_gha_min_cost._calculate_job_cost"
        )
        mock_calculate_job_cost.side_effect = [
            0.008, 
            0.016,
            0.024,  
        ]
        minutes_for_run, cost_for_run = _calculate_gha_run_minutes_and_cost(
            mock_jobs, os_multipliers, minute_cost_usd)
        
        assert minutes_for_run == 6.0
        assert cost_for_run == 0.048
        mock_calculate_job_cost.call_count == 3
       
    def test_calculcate_gha_repo_minutes_and_cost(self, mocker): 
        
        mock_repo = Mock()
        mock_github_service = mocker.patch("services.github_service.GithubService")
        mock_calculate_gha_run_minutes_and_cost = mocker.patch(
            "bin.fetch_gha_min_cost._calculate_gha_run_minutes_and_cost"
        )
        
        mock_workflow_runs_repo_list = [
            Mock(), 
            Mock(),
            Mock()
        ]
        mock_github_service.get_workflow_runs_for_repo.return_value = mock_workflow_runs_repo_list
        mock_calculate_gha_run_minutes_and_cost.side_effect = [
            (10.0, 0.08), 
            (20.0, 1.6),
            (13.0, 0.208),  
        ]
        
        total_minutes, total_cost = _calculcate_gha_repo_minutes_and_cost(
            repo_object=mock_repo, 
            start_date="2024-12-01",
            end_date="2024-12-31",
            github_service=mock_github_service,
            os_multipliers={"UBUNTU": 1, "MACOS": 10, "WINDOWS": 2},
            minute_cost_usd=0.008,
        )
        
        assert total_minutes == 43.0
        assert total_cost == 1.888
 
    def test_process_repository_cost_returned(self, mocker): 
        
        mock_github_service = mocker.patch("services.github_service.GithubService")
        mock_repo = Mock()
        mock_repo.name = "test_repo"
        mock_repo.owner.login = "test_organization"
        mock_workflow_for_repo = Mock()
        mock_workflow_for_repo.totalCount = 5
        mock_github_service.get_workflows_for_repo.return_value = mock_workflow_for_repo
        
        mock_calculcate_gha_repo_minutes_and_cost = mocker.patch(
            "bin.fetch_gha_min_cost._calculcate_gha_repo_minutes_and_cost"
        )
        mock_calculcate_gha_repo_minutes_and_cost.return_value = (120.0, 10.350)
        
        repo_costs = _process_repository(repo_object=mock_repo, start_date="2025-01-02T00:00:00Z",
            end_date="2025-01-09T00:00:00Z", github_service=mock_github_service,
            os_multipliers={"UBUNTU": 1, "MACOS": 10, "WINDOWS": 2},
            minute_cost_usd=0.008)
        
        assert repo_costs['start_datetime']=="2025-01-02T00:00:00Z"
        assert repo_costs['end_datetime']=="2025-01-09T00:00:00Z"
        assert repo_costs["gha_minutes_usage_min"]==120.0
        assert repo_costs["gha_minutes_cost_usd"]==10.350
        assert repo_costs["repo_name"]=="test_repo"
        assert repo_costs[ "organization"]=="test_organization"

    def test_process_repository_cost_zero_returned(self, mocker):
        
        mock_github_service = mocker.patch("services.github_service.GithubService")
        mock_repo = Mock()
        mock_repo.name = "test_repo"
        mock_repo.owner.login = "test_organization"
        mock_workflow_for_repo = Mock()
        mock_workflow_for_repo.totalCount = 5
        mock_github_service.get_workflows_for_repo.return_value = mock_workflow_for_repo
        
        mock_calculcate_gha_repo_minutes_and_cost = mocker.patch(
            "bin.fetch_gha_min_cost._calculcate_gha_repo_minutes_and_cost"
        )
        mock_calculcate_gha_repo_minutes_and_cost.return_value = (120.0, 0.0)
        
        repo_costs = _process_repository(repo_object=mock_repo, start_date="",
            end_date="2024-12-31", github_service=mock_github_service,
            os_multipliers={"UBUNTU": 1, "MACOS": 10, "WINDOWS": 2},
            minute_cost_usd=0.008)
        
        assert repo_costs==None
        
    def test_process_repository_no_workflows_returned(self, mocker):
        
        mock_github_service = mocker.patch("services.github_service.GithubService")
        mock_repo = Mock()
        mock_repo.name = "test_repo"
        mock_repo.owner.login = "test_organization"
        mock_workflow_for_repo = Mock()
        mock_workflow_for_repo.totalCount = 0
        mock_github_service.get_workflows_for_repo.return_value = mock_workflow_for_repo
        
        repo_costs = _process_repository(repo_object=mock_repo, start_date="2025-01-02T00:00:00Z",
            end_date="2025-01-0T00:00:00Z", github_service=mock_github_service,
            os_multipliers={"UBUNTU": 1, "MACOS": 10, "WINDOWS": 2},
            minute_cost_usd=0.008)
        
        assert repo_costs==None
        

    def test_run_thread_pool_processing(self, mocker): 
        
        mock_github_service = mocker.patch("services.github_service.GithubService")
        mock_process_repository = mocker.patch(
            "bin.fetch_gha_min_cost._process_repository"
        )
        mock_process_repository.side_effect = [
            {"start_datetime": "2025-01-02T00:00:00Z", "end_datetime": "2025-01-09T00:00:00Z", "repo_name": "repo1", "gha_minutes_usage_min": 1200, "gha_minutes_cost_usd": 9.6, "organization": "org1"},
            {"start_datetime": "2025-01-02T00:00:00Z", "end_datetime": "2025-01-09T00:00:00Z", "repo_name": "repo2", "gha_minutes_usage_min": 625, "gha_minutes_cost_usd": 5.0, "organization": "org2"},
            {"start_datetime": "2025-01-02T00:00:00Z", "end_datetime": "2025-01-09T00:00:00Z", "repo_name": "repo1", "gha_minutes_usage_min": 1500, "gha_minutes_cost_usd": 12.0, "organization": "org1"}
            ]
        mock_repo_obj_list = [Mock(), Mock(), Mock()]
    
        result = _run_thread_pool_processing(
            repo_obj_list=mock_repo_obj_list,
            start_date="2025-01-02T00:00:00Z",
            end_date="2025-01-09T00:00:00Z",
            github_service=mock_github_service,
            os_multipliers={"UBUNTU": 1, "MACOS": 10, "WINDOWS": 2},
            minute_cost_usd=0.008)
        
        assert {"start_datetime": "2025-01-02T00:00:00Z", "end_datetime": "2025-01-09T00:00:00Z", "repo_name": "repo1", "gha_minutes_usage_min": 1200, "gha_minutes_cost_usd": 9.6, "organization": "org1"} in result
        assert {"start_datetime": "2025-01-02T00:00:00Z", "end_datetime": "2025-01-09T00:00:00Z", "repo_name": "repo2", "gha_minutes_usage_min": 625, "gha_minutes_cost_usd": 5.0, "organization": "org2"} in result
        assert {"start_datetime": "2025-01-02T00:00:00Z", "end_datetime": "2025-01-09T00:00:00Z", "repo_name": "repo1", "gha_minutes_usage_min": 1500, "gha_minutes_cost_usd": 12.0, "organization": "org1"} in result
    
    def test_fetch_gha_usage_data(self, mocker):
    
        mock_get_environment_variables = mocker.patch(
            "bin.fetch_gha_min_cost._get_environment_variables"
        )
        mock_github_service = mocker.patch("bin.fetch_gha_min_cost.GithubService")
        mock_get_environment_variables.return_value = ("mock_moj_token", "mock_ap_token")
        mock_run_thread_pool_processing = mocker.patch("bin.fetch_gha_min_cost._run_thread_pool_processing")
        mock_github_service.get_all_private_non_archived_repos.return_value = [Mock(), Mock()]
        mock_github_service.get_all_internal_non_archived_repos.return_value = [Mock(), Mock(), Mock()]
        
        fetch_gha_usage_data(minute_cost_usd=0.008, period_days=7, os_multipliers={"UBUNTU": 1, "MACOS": 10, "WINDOWS": 2})
        
        assert mock_get_environment_variables.call_count == 1
        assert mock_run_thread_pool_processing.call_count == 2
