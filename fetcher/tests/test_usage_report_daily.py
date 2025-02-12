from datetime import datetime, timedelta
import pytest
from bin.fetch_usage_report_daily import _get_environment_variables, fetch_usage_report_daily


class TestFetchGithubActionsQuota:

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

    def test_fetch_usage_report_daily(self, mocker):

        mock_get_environment_variables = mocker.patch(
            "bin.fetch_usage_report_daily._get_environment_variables"
        )
        mock_get_environment_variables.return_value = "token_mock"
        mock_get_current_daily_usage_for_enterprise = mocker.patch(
            "bin.fetch_usage_report_daily.GithubService.get_current_daily_usage_for_enterprise")

        fetch_usage_report_daily()

        yesterday = (datetime.today() - timedelta(days=1)).day

        mock_get_environment_variables.assert_called_once()
        mock_get_current_daily_usage_for_enterprise.assert_called_with(day=yesterday) 
