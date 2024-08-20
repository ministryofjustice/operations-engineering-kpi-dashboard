import logging

from flask import Blueprint, redirect

logger = logging.getLogger(__name__)

index_route = Blueprint("index_routes", __name__)

@index_route.route("/")
def add_indicator():
    return redirect("/dashboard/", 302)
