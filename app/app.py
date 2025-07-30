import logging
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

    return dashboard
