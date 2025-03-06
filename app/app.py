import logging
from datetime import datetime
from dash import Dash, dcc, html
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
    app.layout = create_dashboard(server.figure_service)

    if app_config.auth_enabled:
        auth = OIDCAuth(
            app,
            secret_key=app_config.flask.app_secret_key,
            force_https_callback=True,
            secure_session=True,
        )
        add_public_routes(app, routes=["/api/indicator/add",
                                       "/api/github_usage_report/add",
                                       "/api/github_repository_metadata/add"])
        auth.register_provider(
            "idp",
            token_endpoint_auth_method="client_secret_post",
            client_id=app_config.auth0.client_id,
            client_secret=app_config.auth0.client_secret,
            server_metadata_url=f"https://{app_config.auth0.domain}/.well-known/openid-configuration",
        )
    logger.info("Running app...")

    return app.server


def create_dashboard(figure_service: FigureService):
    def dashboard():
        available_gh_usage_years = figure_service.database_service.get_github_usage_available_years()
        available_gh_usage_years_int = [int(row[0]) for row in available_gh_usage_years]
        available_gh_usage_months = figure_service.database_service.get_github_usage_available_months()
        available_gh_usage_months_int = [int(row[0]) for row in available_gh_usage_months]
        current_year = datetime.now().year
        current_month = datetime.now().month
        moj_organisations = ["ministryofjustice", "moj-analytical-services",
                             "CriminalInjuriesCompensationAuthority"]
        return html.Div(
            children=[
                html.H1("🤩 Live Data 🤩"),
                dcc.Graph(
                    figure=figure_service.get_number_of_repositories_with_standards_label_dashboard(),
                    style={
                        "width": "100%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
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
                html.H2("Sentry Quota"),
                dcc.Graph(
                    figure=figure_service.get_sentry_transactions_usage(),
                    style={
                        "width": "100%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                dcc.Graph(
                    figure=figure_service.get_sentry_errors_usage(),
                    style={
                        "width": "50%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                dcc.Graph(
                    figure=figure_service.get_sentry_replays_usage(),
                    style={
                        "width": "50%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),

                html.H2("Github Actions Quota"),
                dcc.Graph(
                    figure=figure_service.get_github_actions_quota_usage_cumulative()[0],
                    style={
                        "width": "100%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                dcc.Graph(
                    figure=figure_service.get_github_actions_quota_usage_cumulative()[1],
                    style={
                        "width": "100%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                html.H2("Github Actions Spending"),
                html.Div([
                    html.Label("Year:", style={'color': 'white', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        options=[{'label': str(year), 'value': year} for year in available_gh_usage_years_int],
                        value=current_year,
                        placeholder="Select a year",
                        style={'width': '200px', 'margin-right': '20px'}),
                    
                    html.Label("Month:", style={'color': 'white', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        options=[{'label': 'All', 'value': 'all'}] + [
                            {'label': str(month), 'value': month} for month in available_gh_usage_months_int],
                        value=current_month,
                        placeholder="Select a month",
                        style={'width': '200px'}
                        ),
                    ],
                        style={'display': 'flex', 'align-items': 'center'}),
                dcc.Graph(
                    figure=figure_service.get_gh_minutes_spending_charts(
                        current_year, current_month)[0],
                    style={
                        "width": "30%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                dcc.Graph(
                    figure=figure_service.get_gh_minutes_spending_charts(
                        current_year, current_month)[1],
                    style={
                        "width": "70%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                html.Div([
                    html.Label("Organisation:", style={'color': 'white', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        options=[{'label': org, 'value': org} for org in moj_organisations],
                        value=moj_organisations[0],
                        placeholder="Select an organisation",
                        style={'width': '200px', 'margin-right': '20px'}
                        ),
                    dcc.Graph(
                        figure=figure_service.get_gh_minutes_spending_charts(
                            current_year, current_month, moj_organisations[0])[2],
                        style={
                            "width": "100%",
                             "height": "500px",
                            "display": "inline-block",
                        },
                    ),
                    ], style={'display': 'flex', 'flexDirection': 'column'}),

                html.H1("🙈 Stub Data 🙈"),
                dcc.Graph(
                    figure=figure_service.get_stubbed_number_of_repositories_with_standards_label_dashboard(),
                    style={
                        "width": "33%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                dcc.Graph(
                    figure=figure_service.get_stubbed_number_of_repositories_archived_by_automation(),
                    style={
                        "width": "33%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                dcc.Graph(
                    figure=figure_service.get_stubbed_sentry_transactions_used(),
                    style={
                        "width": "33%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
                dcc.Graph(
                    figure=figure_service.get_support_stats(),
                    style={
                        "width": "100%",
                        "height": "500px",
                        "display": "inline-block",
                    },
                ),
            ],
            style={"padding": "0px", "margin": "0px", "background-color": "black"},
        )

    return dashboard
