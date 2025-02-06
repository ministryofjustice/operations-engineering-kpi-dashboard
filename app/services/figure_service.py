import logging

import pandas as pd
from datetime import date, timedelta
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

    def get_github_actions_quota_usage_cumulative(self):

        github_actions_quota_usage_cumulative = pd.DataFrame(
            self.database_service.get_indicator(
                "ENTERPRISE_GITHUB_ACTIONS_QUOTA_USAGE"
            ),
            columns=["timestamp", "count"],
        ).sort_values(by="timestamp", ascending=True)


        fig_github_actions_quota_usage_cumulative = px.line(
            github_actions_quota_usage_cumulative,
            x="timestamp",
            y="count",
            title="Cumulative Github Actions Usage",
            markers=True,
            template="plotly_dark",
        )
        fig_github_actions_quota_usage_cumulative.add_hline(
            y=50000,
            line=dict(color="red", dash="dash"),
            annotation_text="Minutes allowance",
            annotation_position="top right"
        )
        fig_github_actions_quota_usage_cumulative.update_layout(
            yaxis_title="Min used"
        )

        if github_actions_quota_usage_cumulative.shape[0] < 1: 
            return fig_github_actions_quota_usage_cumulative, None

        # Add quota reset lines
        start_date = github_actions_quota_usage_cumulative['timestamp'].min().date()
        end_date = github_actions_quota_usage_cumulative['timestamp'].max().date()
        max_y = github_actions_quota_usage_cumulative['count'].max()

        start_days_quota = pd.date_range(start=start_date, end=end_date, freq='MS')

        for day in start_days_quota:
            fig_github_actions_quota_usage_cumulative.add_vline(
                x=day,
                line_dash="dash",
                line_color="white"
                )
            fig_github_actions_quota_usage_cumulative.add_annotation(
                x=day, y=max_y, text="Quota Reset", ax=-25)

        # Daily gha consumption graph
        github_actions_quota_usage_daily = github_actions_quota_usage_cumulative.copy()
        github_actions_quota_usage_daily['Month'] = github_actions_quota_usage_daily['timestamp'].dt.to_period('M')
        github_actions_quota_usage_daily['Daily_minutes'] = github_actions_quota_usage_daily.groupby('Month')['count'].diff()
        github_actions_quota_usage_daily['Date'] = (github_actions_quota_usage_daily['timestamp'] - timedelta(days=1)).dt.date

        github_actions_quota_usage_daily = github_actions_quota_usage_daily.dropna()

        fig_github_actions_quota_usage_daily = px.bar(
            github_actions_quota_usage_daily,
            x="Date",
            y="Daily_minutes",
            title="Daily Github Actions Usage",
            template="plotly_dark",
        )
        fig_github_actions_quota_usage_daily.update_layout(
            yaxis_title="Min used"
        )
        if github_actions_quota_usage_daily.shape[0] > 0:
            fig_github_actions_quota_usage_daily.add_hline(
                y=github_actions_quota_usage_daily['Daily_minutes'].median(),
                line=dict(color="red", dash="dash"),  # Custom line style
                annotation_text="Median",
                annotation_position="top right"
            )

        return fig_github_actions_quota_usage_cumulative, fig_github_actions_quota_usage_daily

    def get_sentry_transactions_usage(self):
        sentry_transaction_quota_consumed = pd.DataFrame(
            self.database_service.get_indicator(
                "SENTRY_TRANSACTIONS_USED_OVER_PAST_DAY"
            ),
            columns=["timestamp", "count"],
        ).sort_values(by="timestamp", ascending=True)

        fig_stubbed_sentry_transactions_used = px.line(
            sentry_transaction_quota_consumed,
            x="timestamp",
            y="count",
            title="Sentry Transactions Used",
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

    def get_sentry_errors_usage(self):
        sentry_errors_quota_consumed = pd.DataFrame(
            self.database_service.get_indicator("SENTRY_ERRORS_USED_OVER_PAST_DAY"),
            columns=["timestamp", "count"],
        ).sort_values(by="timestamp", ascending=True)

        fig_sentry_erros_used = px.line(
            sentry_errors_quota_consumed,
            x="timestamp",
            y="count",
            title="Errors Used",
            markers=True,
            template="plotly_dark",
        )
        fig_sentry_erros_used.add_hline(y=129032, annotation_text="Max Daily Usage")
        fig_sentry_erros_used.add_hrect(
            y0=(129032 * 0.8),
            y1=129032,
            line_width=0,
            fillcolor="red",
            opacity=0.2,
            annotation_text="Alert Threshold",
        )

        return fig_sentry_erros_used

    def get_sentry_replays_usage(self):
        sentry_replays_quota_consumed = pd.DataFrame(
            self.database_service.get_indicator("SENTRY_REPLAYS_USED_OVER_PAST_DAY"),
            columns=["timestamp", "count"],
        ).sort_values(by="timestamp", ascending=True)

        fig_sentry_replays_used = px.line(
            sentry_replays_quota_consumed,
            x="timestamp",
            y="count",
            title="Replays Used",
            markers=True,
            template="plotly_dark",
        )
        fig_sentry_replays_used.add_hline(y=25806, annotation_text="Max Daily Usage")
        fig_sentry_replays_used.add_hrect(
            y0=(25806 * 0.8),
            y1=25806,
            line_width=0,
            fillcolor="red",
            opacity=0.2,
            annotation_text="Alert Threshold",
        )

        return fig_sentry_replays_used
