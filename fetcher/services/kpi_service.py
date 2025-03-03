import logging
from typing import Dict
from datetime import datetime

import requests
from requests import Response

logger = logging.getLogger("myapp")
logging.basicConfig()


class KpiService:
    # Added to stop TypeError on instantiation. See https://github.com/python/cpython/blob/d2340ef25721b6a72d45d4508c672c4be38c67d3/Objects/typeobject.c#L4444
    def __new__(cls, *args, **kwargs):
        return super(KpiService, cls).__new__(cls)

    def __init__(self, base_url: str, api_key: str):
        self.__base_url = base_url
        self.__request_headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        self.__request_timeout = 10

    def __post(self, endpoint: str, data: Dict) -> Response:
        return requests.post(
            url=f"{self.__base_url}{endpoint}",
            headers=self.__request_headers,
            timeout=self.__request_timeout,
            json=data,
        )

    def track_github_usage_report_daily(self, report_date: datetime.date, report_usage_data: dict):
        self.__post("/api/github_usage_report/add", {"report_date": report_date, "report_usage_data": report_usage_data})

    def post_github_repository_metadata(self, github_id: int, name: str, full_name: str, owner: str, visibility: str):
        self.__post("/api/github_repository_metadata/add",
                    {"github_id": github_id, "name": name,"full_name": full_name, "owner": owner, "visibility": visibility})