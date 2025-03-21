import logging
from typing import Union
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go

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
        current_year = datetime.now().year

        support_requests_all = pd.read_csv("production/support_request_stats.csv")
        support_requests_all["Date"] = pd.to_datetime(support_requests_all["Date"])
        support_requests_all["Year"] = support_requests_all["Date"].dt.year
        support_requests_all["Month Number"] = support_requests_all["Date"].dt.month
        support_requests_all["Month"] = support_requests_all["Date"].dt.month
        support_requests_all["Month"] = pd.to_datetime(
            support_requests_all["Month"], format="%m"
        ).dt.month_name()

        support_requests_filtered = support_requests_all.query("Year == @current_year")

        support_requests_year_to_date = (
            support_requests_filtered.groupby(by=["Month Number", "Month", "Type"])
            .size()
            .reset_index(name="Count")
        )

        fig_support_stats_year_to_date = px.line(
            support_requests_year_to_date,
            x="Month",
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
            annotation_position="top right",
        )
        fig_github_actions_quota_usage_cumulative.update_layout(yaxis_title="Min used")

        if github_actions_quota_usage_cumulative.shape[0] < 1:
            return fig_github_actions_quota_usage_cumulative, None

        # Add quota reset lines
        start_date = github_actions_quota_usage_cumulative["timestamp"].min().date()
        end_date = github_actions_quota_usage_cumulative["timestamp"].max().date()
        max_y = github_actions_quota_usage_cumulative["count"].max()

        start_days_quota = pd.date_range(start=start_date, end=end_date, freq="MS")

        for day in start_days_quota:
            fig_github_actions_quota_usage_cumulative.add_vline(
                x=day, line_dash="dash", line_color="white"
            )
            fig_github_actions_quota_usage_cumulative.add_annotation(
                x=day, y=max_y, text="Quota Reset", ax=-25
            )

        # Daily gha consumption graph
        github_actions_quota_usage_daily = github_actions_quota_usage_cumulative.copy()
        github_actions_quota_usage_daily["Month"] = github_actions_quota_usage_daily[
            "timestamp"
        ].dt.to_period("M")
        github_actions_quota_usage_daily["Daily_minutes"] = (
            github_actions_quota_usage_daily.groupby("Month")["count"].diff()
        )
        github_actions_quota_usage_daily["Date"] = (
            github_actions_quota_usage_daily["timestamp"] - timedelta(days=1)
        ).dt.date

        github_actions_quota_usage_daily = github_actions_quota_usage_daily.dropna()

        fig_github_actions_quota_usage_daily = px.bar(
            github_actions_quota_usage_daily,
            x="Date",
            y="Daily_minutes",
            title="Daily Github Actions Usage",
            template="plotly_dark",
        )
        fig_github_actions_quota_usage_daily.update_layout(yaxis_title="Min used")
        if github_actions_quota_usage_daily.shape[0] > 0:
            fig_github_actions_quota_usage_daily.add_hline(
                y=github_actions_quota_usage_daily["Daily_minutes"].median(),
                line=dict(color="red", dash="dash"),  # Custom line style
                annotation_text="Median",
                annotation_position="top right",
            )

        return (
            fig_github_actions_quota_usage_cumulative,
            fig_github_actions_quota_usage_daily,
        )

    def get_gh_minutes_spending_charts(
        self, year: int, month: Union[int, str], org_per_repo: str = None
    ):

        def return_empty_graphs():
            empty_df = pd.DataFrame({"x": [], "y": []})

            empty_total_chart = go.Figure(
                go.Indicator(
                    mode="number+delta",
                    value=None,  # No value, making it empty
                    number={"prefix": "$"},
                    delta={"position": "top", "reference": 320},
                    domain={"x": [0, 1], "y": [0, 1]},
                )
            )

            empty_pie_chart = px.pie(
                empty_df,
                names="x",
                values="y",
                template="plotly_dark",
                title="No Data Available",
            )
            empty_area_chart = px.area(
                empty_df,
                x="x",
                y="y",
                template="plotly_dark",
                title="No Data Available",
            )
            empty_bar_chart = px.bar(
                empty_df,
                x="x",
                y="y",
                template="plotly_dark",
                title="No Data Available",
            )

            return {
                "total_spending_chart": empty_total_chart,
                "pie_chart_gross_spending": empty_pie_chart,
                "area_chart_spending_trends": empty_area_chart,
                "bar_chart_repository_spending": empty_bar_chart,
            }

        data_usage_df = pd.DataFrame(
            self.database_service.get_github_usage_report(year, month),
            columns=["report_date", "created_at", "report_usage_data"],
        ).sort_values(by="report_date", ascending=True)

        if data_usage_df.empty:
            return return_empty_graphs()

        data_usage_df["usageItems"] = data_usage_df["report_usage_data"].apply(
            lambda x: x["usageItems"]
        )
        df_filtered = data_usage_df[
            data_usage_df["usageItems"].apply(lambda x: len(x) > 0)
        ]

        if df_filtered.empty:
            return return_empty_graphs()

        df_exploded = df_filtered.explode("usageItems")
        df_normalized = pd.json_normalize(df_exploded["usageItems"])
        df_total_gh_usage = (
            df_exploded[["report_date", "created_at"]]
            .reset_index(drop=True)
            .join(df_normalized)
        )
        df_gh_minutes_usage = df_total_gh_usage.loc[
            df_total_gh_usage["unitType"] == "Minutes"
        ]

        repos_list = [
            repo[0] for repo in self.database_service.get_private_internal_repos()
        ]
        df_gh_minutes_paid = df_gh_minutes_usage.loc[
            df_gh_minutes_usage["repositoryName"].isin(repos_list)
        ]

        if df_gh_minutes_paid.empty:
            return return_empty_graphs()

        df_gh_minutes_by_org_daily = (
            df_gh_minutes_paid.groupby(["report_date", "organizationName"])[
                "grossAmount"
            ]
            .sum()
            .reset_index()
            .sort_values(by=["report_date"])
        )

        df_gh_minutes_org_totals = (
            df_gh_minutes_paid.groupby("organizationName")["grossAmount"]
            .sum()
            .reset_index()
        )

        df_org_per_repo = df_gh_minutes_paid.loc[
            df_gh_minutes_paid["organizationName"] == org_per_repo
        ]

        df_org_per_repo_group = (
            df_org_per_repo.groupby(["repositoryName"])["grossAmount"]
            .sum()
            .reset_index()
        )
        df_org_per_repo_group = df_org_per_repo_group.sort_values(
            by=["grossAmount"], ascending=False
        )

        fig_total = go.Figure(
            go.Indicator(
                mode="number+delta",
                value=df_gh_minutes_paid["grossAmount"].sum(),
                number={"prefix": "$"},
                domain={"x": [0, 1], "y": [0, 1]},
            )
        )
        fig_total.update_layout(template="plotly_dark", title="Total Gross Amount")

        fig_gh_minutes_org_totals = px.pie(
            df_gh_minutes_org_totals,
            names="organizationName",
            values="grossAmount",
            title="Github Action Gross Spending by Organisation",
            template="plotly_dark",
            labels={
                "organizationName": "Organisation",
                "grossAmount": "Spending (USD)",
            },
        )

        fig_gh_miniutes_by_org = px.area(
            df_gh_minutes_by_org_daily,
            x="report_date",
            y="grossAmount",
            color="organizationName",
            title="Github Actions Spending Trends by Organisation",
            template="plotly_dark",
            labels={"report_date": "Date", "grossAmount": "Spending (USD)"},
        )

        fig_per_repo = px.bar(
            df_org_per_repo_group,
            x="repositoryName",
            y="grossAmount",
            color="repositoryName",
            title="Github Actions Spending by Repository",
            template="plotly_dark",
            labels={"repositoryName": "Repository", "grossAmount": "Spending (USD)"},
        )

        fig_per_repo.update_xaxes(showticklabels=False)

        return {
            "total_spending_chart": fig_total,
            "pie_chart_gross_spending": fig_gh_minutes_org_totals,
            "area_chart_spending_trends": fig_gh_miniutes_by_org,
            "bar_chart_repository_spending": fig_per_repo,
        }

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
