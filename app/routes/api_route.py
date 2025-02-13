import logging
from typing import Callable
from functools import wraps

from flask import Blueprint, current_app, request

from app.config.app_config import app_config

logger = logging.getLogger(__name__)

api_route = Blueprint("api_routes", __name__)


def requires_api_key(func: Callable):
    @wraps(func)
    def decorator(*args, **kwargs):
        if "X-API-KEY" not in request.headers or request.headers.get("X-API-KEY") != app_config.api_key:
            return "", 403
        return func(*args, **kwargs)

    return decorator


@api_route.route("/indicator/add", methods=["POST"])
@requires_api_key
def add_indicator():
    indicator = request.get_json().get("indicator")
    count = request.get_json().get("count")
    current_app.database_service.add_indicator(indicator, count)
    return ("", 204)


@api_route.route("/github_usage_report/add", methods=["POST"])
@requires_api_key
def add_github_usage_report():
    report_date = request.get_json().get("report_date")
    report_usage_data = request.get_json().get("report_usage_data")
    current_app.database_service.add_github_usage_report(report_date, report_usage_data)
    return ("", 204)
