from datetime import datetime, timedelta
from unittest.mock import MagicMock
import pytest
from bin.fetch_gh_repos_metadata import _get_environment_variables, fetch_gh_repos_metadata


class TestFetchGhReposMetadata:

    def test_get_environment_variables(self, mocker):

        mock_getenv = mocker.patch("os.getenv")
        mock_getenv.return_value = "token_mock"

        result = _get_environment_variables()

        assert result == "token_mock"

    def test_get_environment_variables_missing_token(self, mocker):

        mock_getenv = mocker.patch("os.getenv")
        mock_getenv.return_value = None

        with pytest.raises(ValueError) as err:
            _get_environment_variables()

        assert str(err.value) == (
            "The env variable GH_TOKEN is empty or missing"
        )
        
    def test_fetch_gh_repos_metadata(self, mocker):
        
        mock_get_environment_variables = mocker.patch(
            "bin.fetch_gh_repos_metadata._get_environment_variables")
        mock_get_environment_variables.return_value = "token_mock"
        mock_get_organisation_for_enterprise = mocker.patch(
            "bin.fetch_gh_repos_metadata.GithubService.get_all_organisations_in_enterprise")
        mock_orgs=["org1"]
        mock_get_organisation_for_enterprise.return_value = mock_orgs
        mock_gh_service_get_all_repos = mocker.patch("bin.fetch_gh_repos_metadata.GithubService.get_non_archived_repos")

        mock_repo_1 = MagicMock()
        mock_repo_1.id = 1
        mock_repo_1.name = 'test-repo-1'
        mock_repo_1.full_name = 'org1/test-repo'
        mock_repo_1.owner.login = 'test-owner-1'
        mock_repo_1.visibility = 'public'
        mock_repo_2 = MagicMock()
        mock_repo_2.id = 2
        mock_repo_2.name = 'test-repo-2'
        mock_repo_2.full_name = 'org2/test-repo-2'
        mock_repo_2.owner.login = 'test-owner-2'
        mock_repo_2.visibility = 'internal'

        mock_gh_service_get_all_repos.return_value = [mock_repo_1, mock_repo_2]

        mock_kpi_service = mocker.patch(
            "bin.fetch_gh_repos_metadata.KpiService.post_github_repository_metadata")

        fetch_gh_repos_metadata()

        mock_get_environment_variables.assert_called_once()
        mock_gh_service_get_all_repos.assert_called_once_with(org_name="org1")
        assert mock_kpi_service.call_count == 2