import logging
import pandas as pd
from datetime import datetime, date
import plotly.express as px

logger = logging.getLogger(__name__)


class FigureService:
    def __init__(self, database_service) -> None:
        self.database_service = database_service
