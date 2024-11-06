import sys
from botocore.client import BaseClient
from botocore.exceptions import ClientError, NoCredentialsError
import boto3
import os
from datetime import datetime
from mojap_metadata import Metadata
from mojap_metadata.converters.glue_converter import GlueConverter

timestamp = datetime.now().strftime("%Y%m%d%H%M")
print(timestamp)

table_name = "support_request_stats"

read_path = "/data/production"

# [f"./data{tn}/{tn}.csv" for tn in table_names]

write_path = [f"/data/production/{timestamp}/support_request_stats.csv"]
print(write_path)

# Set up AWS clients
s3_client = boto3.client("s3")
glue_client = boto3.client("glue")

# Set up for creating database and tables
# destination bucket, database name, data locations, metadata
bucket = "operations-engineering-support-request-stats"
db_name = "support_request_data"

# set data location to the dir containing the sub dirs of release versions
# so that update_table will see all the new versions when it runs
data_locations = [f"s3://{bucket}/data/production/{timestamp}/"]
# for tn in table_name]
meta_paths = [f"./data/{timestamp}.json"]
# for tn in table_name]


# Function to write data to bucket
def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client("s3")
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except (ClientError, NoCredentialsError) as e:
        print(e)
        raise
    return print("file uploaded")


# Function to check if database exists
def does_database_exist(client, database_name):
    """Determine if this database exists in the Data Catalog
    The Glue client will raise an exception if it does not exist.
    """
    try:
        client.get_database(Name=database_name)
        return True
    except client.exceptions.EntityNotFoundException:
        return False


# Function to check if table exists
def does_table_exist(client, database_name, table_name):
    """Determine if this table exists in the Data Catalog
    The Glue client will raise an exception if it does not exist.
    """
    try:
        client.get_table(DatabaseName=database_name, Name=table_name)
        return True
    except client.exceptions.EntityNotFoundException:
        return False


# Upload files to bucket
for rp, wp in zip(read_path, write_path):
    upload_file(file_name=rp, bucket=bucket, object_name=wp)

# Create database if it does not exist
if not does_database_exist(glue_client, db_name):
    print("create database")
    glue_client.create_database(
        DatabaseInput={
            "Name": db_name,
            "Description": "A database for Operations Engineering support request data",
        }
    )

# Create table if it does not exist, else update
for metadata, data_location in zip(meta_paths, data_locations):

    # Check
    print("Metadata path: ", metadata)
    print("Data location: ", data_location)
    # Read metadata from json
    meta = Metadata.from_json(metadata)

    # Create Glue Converter class and set csv friendly params
    gc = GlueConverter()
    gc.options.csv.sep = ","
    gc.options.csv.skip_header = True
    gc.options.csv.quote_char = '"'
    gc.options.csv.escape_char = "\\"
    gc.options.set_csv_serde("open")

    # Generate table meta from json
    boto_dict = gc.generate_from_meta(
        meta, database_name=db_name, table_location=data_location
    )

    # print("boto dict:", boto_dict)
    print("Glue database name: ", boto_dict.get("DatabaseName"))
    print("Glue table name: ", boto_dict.get("TableInput", {}).get("Name"))

    # Check if table exists
    table_exists = does_table_exist(
        glue_client,
        boto_dict.get("DatabaseName"),
        boto_dict.get("TableInput", {}).get("Name"),
    )

    # Check if table exists
    print("TABLE EXISTS: ", table_exists)

    # Create table if exists, else update
    if not table_exists:
        print("creating table")
        glue_client.create_table(**boto_dict)
    else:
        print("updating table")
        glue_client.update_table(**boto_dict)
