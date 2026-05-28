import logging
import os
from transform import transform
from load import load_data
from load_sql import load_sql

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "etl.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


if __name__ == "__main__":
    # Start the ETL pipeline
    logging.info("Starting ETL pipeline")

    load_dfs = transform()

    load_data(load_dfs)


    logging.info(
        "ETL completed | imported=%d | flagged=%d",
        len(load_dfs["output"]["journal_import"]),
        len(load_dfs["output"]["journal_flagged"])
    )

