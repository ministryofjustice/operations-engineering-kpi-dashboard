import logging
import os

import boto3
from botocore.exceptions import NoCredentialsError

BUCKET_NAME = "operations-engineering-support-requests-stats-csv"
CSV_FILE_NAME = "support_request_stats.csv"
FILEPATH = "/data/production/"
MOJ_ORGANISATION = "ministryofjustice"


def upload_support_request_stats_to_s3():
    s3 = boto3.client("s3")
    try:
        s3.upload_file(FILEPATH, CSV_FILE_NAME, BUCKET_NAME)
        logger.info("File %s uploaded succesfully.", CSV_FILE_NAME)
    except NoCredentialsError:
        logger.error("Credentials not available, please check your AWS credentials.")
    except FileNotFoundError as e:
        logger.error("Error uploading file: %s", e)
    if not os.path.isfile(CSV_FILE_NAME):
        raise FileNotFoundError(
            f"File {CSV_FILE_NAME} not found in the current directory."
        )
