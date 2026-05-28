import logging
import os
import urllib
import yaml
# from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

with open('config.yaml', 'r') as f:
    CONFIG = yaml.safe_load(f)

DATABASES = CONFIG["DATABASES"]
QUERIES = CONFIG["QUERIES"]

# load_dotenv()

# Build SQLAlchemy engine
def get_engine(db_config):
    logging.info(
        "Creating SQL engine for server, database=%s",
        db_config["db"]
    )
    driver = db_config["driver"]
    server = db_config["server"]
    database = db_config["db"]
    # user = db_config["user"]
    # password = db_config["password"]

    conn_str = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection=yes;"
        # f"UID={user};"
        # f"PWD={password}"
    )

    # URL‑encode
    encoded = urllib.parse.quote_plus(conn_str)

    # Build SQLAlchemy engine. dialect+driver://username:password@host:port/database
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={encoded}")

    logging.info("Engine created successfully")
    return engine


def extract_data(engine, query):
    logging.info("Executing query")

    with engine.connect() as connection:
        result = connection.execute(text(query))
        rows = result.fetchall()
        columns = result.keys()
        df = pd.DataFrame(rows, columns=columns)

    logging.info("Query returned %d rows", len(df))
    return df


def extract():
    logging.info("Starting data extraction from all sources")

    # Create dictionary for source data
    raw_dfs = {}
    for db_name, db_config in DATABASES.items():
        engine = get_engine(db_config)

        for query_name, sql_query in QUERIES[db_name].items():
            logging.info("Running query '%s' for database '%s'", query_name, db_name)
            raw_dfs[query_name] = extract_data(engine, sql_query)

    logging.info("Data extraction complete: %d datasets loaded", len(raw_dfs))
    return raw_dfs