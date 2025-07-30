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
