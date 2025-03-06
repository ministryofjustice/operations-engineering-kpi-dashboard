import datetime
import logging
from typing import Any

import psycopg2

from app.config.app_config import app_config

logger = logging.getLogger(__name__)


class DatabaseService:
    def __execute_query(self, sql: str, values=None):
        with psycopg2.connect(
            dbname=app_config.postgres.db,
            user=app_config.postgres.user,
            password=app_config.postgres.password,
            host=app_config.postgres.host,
            port=app_config.postgres.port,
        ) as conn:
            logging.info("Executing query...")
            cur = conn.cursor()
            cur.execute(sql, values)
            data = None
            if cur.description is not None:
                try:
                    data = cur.fetchall()
                except Exception as e:
                    logging.error(e)
            
            conn.commit()
            return data

    def get_indicator(self, indicator: str) -> list[tuple[Any, Any]]:
        return self.__execute_query(sql="SELECT timestamp, count FROM indicators WHERE indicator = %s;", values=[indicator])

    def create_indicators_table(self) -> None:
        self.__execute_query(
            sql="""
                    CREATE TABLE IF NOT EXISTS indicators (
                        id SERIAL PRIMARY KEY,
                        indicator varchar,
                        timestamp timestamp,
                        count integer
                    );
                """
        )

    def create_github_usage_reports_table(self) -> None:
        self.__execute_query(
            sql="""
                    CREATE TABLE IF NOT EXISTS github_usage_reports (
                        id SERIAL PRIMARY KEY,
                        report_date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        report_usage_data JSONB NOT NULL
                    )
            """
            )

    def create_github_repos_meteadata_table(self) -> None:
        self.__execute_query(
            sql="""
                    CREATE TABLE IF NOT EXISTS github_repos_metadata (
                        github_id INTEGER PRIMARY KEY,
                        name VARCHAR NOT NULL,
                        full_name VARCHAR NOT NULL,
                        owner VARCHAR NOT NULL,
                        visibility VARCHAR NOT NULL
                    )
            """
            )

    def get_private_internal_repos(self) ->list[tuple[Any, Any]]:
        return self.__execute_query(
            sql="""
                SELECT name
                FROM github_repos_metadata
                WHERE visibility = 'private'
                OR visibility = 'internal'
                """
                )

    def get_github_usage_available_years(self) -> list[tuple[Any, Any]]: 
        return self.__execute_query(
            sql="""
                SELECT DISTINCT EXTRACT(YEAR FROM report_date) AS report_year
                FROM github_usage_reports
                ORDER BY report_year;
            """
            )

    def get_github_usage_available_months(self) -> list[tuple[Any, Any]]: 
        return self.__execute_query(
            sql="""
                SELECT DISTINCT EXTRACT(MONTH FROM report_date) AS report_month
                FROM github_usage_reports
                ORDER BY report_month;
            """
        )

    def get_github_usage_report(self, year: int, month: int) -> list[tuple[Any, Any]]:

        if month == "all":
            return self.__execute_query(
                sql="""
                SELECT report_date, created_at, report_usage_data
                FROM github_usage_reports
                WHERE EXTRACT(YEAR FROM report_date) = %s
                """,
                values=(year,))

        else:
            return self.__execute_query(
                sql="""
                SELECT report_date, created_at, report_usage_data
                FROM github_usage_reports
                WHERE EXTRACT(YEAR FROM report_date) = %s
                    AND EXTRACT(MONTH FROM report_date) = %s
                """,
                values=(year, month))

    def clean_stubbed_indicators_table(self) -> None:
        self.__execute_query(sql="DELETE FROM indicators WHERE indicator LIKE 'STUBBED%'")

    def add_indicator(self, indicator, count) -> None:
        self.__execute_query("INSERT INTO indicators (indicator,timestamp, count) VALUES (%s, %s, %s);", values=[indicator, datetime.datetime.now(), count])

    def add_github_repository_metadata(self, github_id: int, name: str, full_name: str, owner: str, visibility: str) -> None:

        self.__execute_query("INSERT INTO github_repos_metadata (github_id, name, full_name, owner, visibility) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (github_id) DO NOTHING;",
                             values=[github_id, name, full_name, owner, visibility])

    def add_github_usage_report(self, report_date, report_usage_data) -> None:
        self.__execute_query("INSERT INTO github_usage_reports (report_date, created_at, report_usage_data) VALUES (%s, %s, %s);", values=[report_date, datetime.datetime.now(), report_usage_data])

    def add_stubbed_indicators(self):
        for values in [
            # SENTRY_DAILY_TRANSACTION_USAGE
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 20), 771761),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 21), 796740),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 22), 437108),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 23), 421906),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 24), 853259),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 25), 779597),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 26), 1249612),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 27), 906111),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 28), 418087),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 29), 413430),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 4, 30), 880825),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 5, 1), 792862),
            ("STUBBED_SENTRY_DAILY_TRANSACTION_USAGE", datetime.date(2024, 5, 1), 783851),
            # REPOSITORIES_WITH_STANDARDS_LABEL
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 20), 11),
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 21), 11),
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 22), 11),
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 23), 11),
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 24), 11),
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 25), 11),
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 26), 11),
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 27), 11),
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 28), 11),
            ("STUBBED_REPOSITORIES_WITH_STANDARDS_LABEL", datetime.date(2024, 4, 29), 11),
            # REPOSITORIES_ARCHIVED_BY_AUTOMATION
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 20), 1),
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 21), 0),
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 22), 0),
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 23), 4),
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 24), 0),
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 25), 0),
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 26), 1),
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 27), 0),
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 28), 0),
            ("STUBBED_REPOSITORIES_ARCHIVED_BY_AUTOMATION", datetime.date(2024, 4, 29), 0),
        ]:
            self.__execute_query("INSERT INTO indicators (indicator,timestamp, count) VALUES (%s, %s, %s);", values=values)
