import logging

import pandas as pd
import datetime
from datetime import date
import plotly.express as px

logger = logging.getLogger(__name__)


class FigureService:
    def __init__(self, database_service) -> None:
        self.database_service = database_service

    def get_number_of_repositories_with_standards_label_dashboard(self):
        number_of_repos_with_standards_label_df = pd.DataFrame(
            self.database_service.get_indicator("REPOSITORIES_WITH_STANDARDS_LABEL"),
            columns=["timestamp", "count"],
        ).sort_values(by="timestamp", ascending=True)

        fig_number_of_repositories_with_standards_label = px.line(
            number_of_repos_with_standards_label_df,
            x="timestamp",
            y="count",
            title="🏷️ Number of Repositories With Standards Label",
            markers=True,
            template="plotly_dark",
        )
        fig_number_of_repositories_with_standards_label.add_hline(y=0)

        return fig_number_of_repositories_with_standards_label

    def get_stubbed_number_of_repositories_with_standards_label_dashboard(self):
        number_of_repos_with_standards_label_df = pd.DataFrame(
            self.database_service.get_indicator(
                "STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL"
            ),
            columns=["timestamp", "count"],
        ).sort_values(by="timestamp", ascending=True)

        fig_stubbed_number_of_repositories_with_standards_label = px.line(
            number_of_repos_with_standards_label_df,
            x="timestamp",
            y="count",
            title="🏷️ Number of Repositories With Standards Label",
            markers=True,
            template="plotly_dark",
        )
        fig_stubbed_number_of_repositories_with_standards_label.add_hline(y=0)

        return fig_stubbed_number_of_repositories_with_standards_label

    def get_stubbed_number_of_repositories_archived_by_automation(self):
        number_of_repositories_archived_by_automation = pd.DataFrame(
            self.database_service.get_indicator(
                "STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION"
            ),
            columns=["timestamp", "count"],
        ).sort_values(by="timestamp", ascending=True)

        fig_stubbed_number_of_repositories_archived_by_automation = px.line(
            number_of_repositories_archived_by_automation,
            x="timestamp",
            y="count",
            title="👴 Number of Repositories Archived By Automation",
            markers=True,
            template="plotly_dark",
        )
        fig_stubbed_number_of_repositories_archived_by_automation.add_hline(y=0)

        return fig_stubbed_number_of_repositories_archived_by_automation

    def get_stubbed_sentry_transactions_used(self):
        sentry_transaction_quota_consumed = pd.DataFrame(
            self.database_service.get_indicator(
                "STUBBED_SENTRY_DAILY_TRANSACTION_USAGE"
            ),
            columns=["timestamp", "count"],
        ).sort_values(by="timestamp", ascending=True)

        fig_stubbed_sentry_transactions_used = px.line(
            sentry_transaction_quota_consumed,
            x="timestamp",
            y="count",
            title="👀 Sentry Transactions Used",
            markers=True,
            template="plotly_dark",
        )
        fig_stubbed_sentry_transactions_used.add_hline(
            y=967741, annotation_text="Max Daily Usage"
        )
        fig_stubbed_sentry_transactions_used.add_hrect(
            y0=(967741 * 0.8),
            y1=967741,
            line_width=0,
            fillcolor="red",
            opacity=0.2,
            annotation_text="Alert Threshold",
        )

        return fig_stubbed_sentry_transactions_used

    def get_support_stats(self):
        support_stats_csv = pd.read_csv("data/support-stats.csv")
        support_stats_csv_pivoted = pd.melt(
            support_stats_csv,
            value_vars=[
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
            id_vars=["Request Type", "Total"],
            value_name="Count",
            var_name="Month",
            ignore_index=True,
        )

        fig_support_stats = px.line(
            support_stats_csv_pivoted,
            x="Month",
            y="Count",
            color="Request Type",
            title="🏋️ Support Stats",
            markers=True,
            template="plotly_dark",
        )

        return fig_support_stats

    def get_support_stats_year_to_date(self):
        support_requests_all = pd.read_csv("production/support_request_stats.csv")
        support_requests_all = (
            support_requests_all.groupby(by=["Date", "Type"])
            .size()
            .reset_index(name="Count")
        )

        fig_support_stats_year_to_date = px.line(
            support_requests_all,
            x="Date",
            y="Count",
            color="Type",
            title="Support Requests by Type - Year to Date",
            template="plotly_dark",
        )

        return fig_support_stats_year_to_date

    def get_support_stats_current_month(self):
        month = date.today().month
        support_requests_current_month = pd.read_csv(
            "production/support_request_stats.csv"
        )
        support_requests_current_month["Date"] = pd.to_datetime(
            support_requests_current_month["Date"], format="%Y-%m-%d"
        )
        support_requests_current_month = support_requests_current_month.loc[
            support_requests_current_month["Date"].dt.month == month
        ]
        support_requests_current_month["Total"] = (
            support_requests_current_month.groupby("Date")["Type"].transform("size")
        )

        fig_support_stats_current_month = px.bar(
            support_requests_current_month,
            x="Date",
            y="Type",
            color="Type",
            title="Support Requests by Type - Current Month",
            template="plotly_dark",
        )

        return fig_support_stats_current_month

    def get_github_actions_quota_usage(self):
        github_usage_csv = pd.read_csv(
            "data/github_actions_private_and_internal.csv"
        ).sort_values(by="Date", ascending=True)
        github_actions = github_usage_csv[github_usage_csv["Product"] == "Actions"]
        github_actions_summed = github_actions.groupby(by="Date", as_index=False).agg(
            "sum"
        )
        github_actions_summed["Date"] = pd.to_datetime(github_actions_summed["Date"])

        fig_github_actions_quota_usage = px.scatter(
            github_actions_summed,
            x="Date",
            y="Quantity",
            title="💥 GitHub Quota Usage",
            trendline="ols",
            template="plotly_dark",
            hover_data=["Price Per Unit ($)"],
        )
        fig_github_actions_quota_usage.add_hline(
            y=(40000 / 31), annotation_text="Max Daily Actions Usage Usage"
        )
        fig_github_actions_quota_usage.add_hrect(
            y0=((40000 / 31) * 0.8),
            y1=(40000 / 31),
            line_width=0,
            fillcolor="red",
            opacity=0.2,
            annotation_text="Actions Alert Threshold",
        )

        return fig_github_actions_quota_usage
