from datetime import datetime, timedelta
import json
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

        mock_report_usage_data = {
            "usageItems": [ { "date": "2023-08-01", "product": "Actions",
                             "sku": "Actions Linux", "quantity": 100, "unitType": "minutes",
                             "pricePerUnit": 0.008, "grossAmount": 0.8, "discountAmount": 0,
                             "netAmount": 0.8, "organizationName": "GitHub", "repositoryName": "github/example"} ] }

        mock_get_current_daily_usage_for_enterprise.return_value = mock_report_usage_data

        mock_kpi_service = mocker.patch(
            "bin.fetch_usage_report_daily.KpiService.track_github_usage_report_daily")


        fetch_usage_report_daily()

        yesterday = (datetime.today() - timedelta(days=1)).date()

        mock_get_environment_variables.assert_called_once()
        mock_get_current_daily_usage_for_enterprise.assert_called_with(month=yesterday.month, day=yesterday.day)
        mock_kpi_service.assert_called_once_with(str(yesterday), json.dumps(mock_report_usage_data))
