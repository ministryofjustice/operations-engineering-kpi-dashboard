import logging
from datetime import datetime
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from dash_auth import OIDCAuth, add_public_routes
from flask import Flask

from app.config.app_config import app_config
from app.config.logging_config import configure_logging
from app.config.routes_config import configure_routes
from app.services.database_service import DatabaseService
from app.services.figure_service import FigureService

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    configure_logging(app_config.logging_level)

    logger.info("Starting app...")

    server = Flask(__name__)

    server.database_service = DatabaseService()
    server.figure_service = FigureService(server.database_service)

    configure_routes(server)

    logger.info("Populating stub data...")
    server.database_service.create_indicators_table()
    server.database_service.create_github_usage_reports_table()
    server.database_service.create_github_repos_meteadata_table()
    server.database_service.clean_stubbed_indicators_table()
    server.database_service.add_stubbed_indicators()

    app = Dash(__name__, server=server, url_base_pathname="/dashboard/")
    app.title = "⚙️ OE - KPI Dashboard"
    app.layout = create_dashboard(server.figure_service, app)

    if app_config.auth_enabled:
        auth = OIDCAuth(
            app,
            secret_key=app_config.flask.app_secret_key,
            force_https_callback=True,
            secure_session=True,
        )
        add_public_routes(
            app,
            routes=[
                "/api/indicator/add",
                "/api/github_usage_report/add",
                "/api/github_repository_metadata/add",
            ],
        )
        auth.register_provider(
            "idp",
            token_endpoint_auth_method="client_secret_post",
            client_id=app_config.auth0.client_id,
            client_secret=app_config.auth0.client_secret,
            server_metadata_url=f"https://{app_config.auth0.domain}/.well-known/openid-configuration",
        )
    logger.info("Running app...")

    return app.server


def create_dashboard(figure_service: FigureService, app: Dash):
    def dashboard():
        available_gh_usage_years = (
            figure_service.database_service.get_github_usage_available_years()
        )
        available_gh_usage_years_int = [int(row[0]) for row in available_gh_usage_years]
        available_gh_usage_months = (
            figure_service.database_service.get_github_usage_available_months()
        )
        available_gh_usage_months_int = [
            int(row[0]) for row in available_gh_usage_months
        ]
        current_year = datetime.now().year
        current_month = datetime.now().month
        moj_organisations = [
            "ministryofjustice",
            "moj-analytical-services",
            "CriminalInjuriesCompensationAuthority",
        ]
        return html.Div(
            children=[
                html.H1("🤩 Live Data 🤩"),
                dcc.Graph(
                    figure=figure_service.get_support_stats_year_to_date(),
                    style={
                        "width": "100%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                dcc.Graph(
                    figure=figure_service.get_support_stats_current_month(),
                    style={
                        "width": "100%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
            ],
            style={"padding": "0px", "margin": "0px", "background-color": "black"},
        )

    @app.callback(
        [
            Output("gh-spending-total", "figure"),
            Output("gh-minutes-gross-spending-graph", "figure"),
            Output("gh-minutes-trends-graph", "figure"),
            Output("gh-minutes-repositories-spending-graph", "figure"),
        ],
        [
            Input("month-dropdown", "value"),
            Input("year-dropdown", "value"),
            Input("organisation-dropdown", "value"),
        ],
    )
    def update_github_spending_graphs(
        selected_month, selected_year, selected_organisation
    ):

        total_spending = figure_service.get_gh_minutes_spending_charts(
            selected_year, selected_month
        ).get("total_spending_chart")
        gross_spending_fig = figure_service.get_gh_minutes_spending_charts(
            selected_year, selected_month
        ).get("pie_chart_gross_spending")
        trends_fig = figure_service.get_gh_minutes_spending_charts(
            selected_year, selected_month
        ).get("area_chart_spending_trends")
        repo_spending_fig = figure_service.get_gh_minutes_spending_charts(
            selected_year, selected_month, selected_organisation
        ).get("bar_chart_repository_spending")
        return total_spending, gross_spending_fig, trends_fig, repo_spending_fig

    return dashboard
