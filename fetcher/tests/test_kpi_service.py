from unittest.mock import call
import pytest
from services.kpi_service import KpiService


TEST_BASE_URL = "https://example.com"
TEST_API_KEY = "your_api_key"


class TestKPIServiceTrackGithubUsageReportDaily:

    def test_api_called(self, mocker):

        mock_request = mocker.patch("services.kpi_service.requests")
        # Create the KpiService instance
        kpi_service = KpiService(TEST_BASE_URL, TEST_API_KEY)

        # Call the method
        kpi_service.track_github_usage_report_daily(
            "2025-02-12", {"test_report": [{"test_atribute": "test_value"},
                                           {"test_atribute2": "test_value2"}]})

        # Assert the correct API call
        mock_request.post.assert_has_calls(
            [
                call(
                    url=f"{TEST_BASE_URL}/api/github_usage_report/add",
                    headers={
                        "X-API-KEY": TEST_API_KEY,
                        "Content-Type": "application/json",
                    },
                    timeout=10,
                    json={
                        "report_date": "2025-02-12",
                        "report_usage_data": {
                            "test_report": [
                                {"test_atribute": "test_value"},
                                {"test_atribute2": "test_value2"}
                                ]
                            }
                        },
                )
            ]
        )
