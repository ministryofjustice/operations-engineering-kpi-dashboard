import logging
import pandas as pd
from datetime import datetime, date
import plotly.express as px

logger = logging.getLogger(__name__)


class FigureService:
    def __init__(self, database_service) -> None:
        self.database_service = database_service

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
