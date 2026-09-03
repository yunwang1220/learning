import json
import logging
import os
from datetime import timedelta
from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import KaggleApi
import snowflake.connector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

MERGE_SQL = """
MERGE INTO LF_DEV.TMP.KAGGLE AS target
USING (SELECT %(ref)s AS ref, %(total_bytes)s AS total_bytes, %(last_updated)s::TIMESTAMP_NTZ AS last_updated) AS source
ON target.ref = source.ref
WHEN MATCHED AND source.last_updated > target.last_updated THEN
    UPDATE SET total_bytes = source.total_bytes, last_updated = source.last_updated
WHEN NOT MATCHED THEN
    INSERT (ref, total_bytes, last_updated) VALUES (source.ref, source.total_bytes, source.last_updated)
"""

load_dotenv()

def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="externalbrowser",
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"]
    )


def load_checkpoint(cursor):
    """Derive checkpoint from MAX(last_updated) in Snowflake."""
    cursor.execute("SELECT MAX(last_updated) FROM LF_DEV.TMP.KAGGLE")
    row = cursor.fetchone()
    checkpoint = row[0] if row else None
    if checkpoint:
        # Apply lookback window to catch late arriving data
        checkpoint = checkpoint - timedelta(hours=24)
        logger.info(f"Checkpoint (with 24hr lookback): {checkpoint}")
    else:
        logger.info("No checkpoint found, running full load.")
    return checkpoint


def yield_kaggle_datasets(api, search_term):
    """Yields individual datasets incrementally from Kaggle."""
    page = 1
    while True:
        try:
            logger.info(f"Fetching page {page} for search term: '{search_term}'")
            batch = api.dataset_list(search=search_term, page=page, sort_by='updated')
        except Exception as e:
            logger.error(f"Failed to fetch page {page}: {e}")
            break

        if not batch:
            logger.info("No more datasets found, stopping.")
            break

        yield from batch
        page += 1

        if page == 101:
            logger.info("Reached page limit, stopping.")
            break

def run(search_term):
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        checkpoint = load_checkpoint(cursor)
        new_records = 0

        for dataset in yield_kaggle_datasets(api, search_term):
            if checkpoint and dataset.last_updated <= checkpoint:
                logger.debug(f"Skipping {dataset.ref}, not updated since checkpoint.")
                continue

            cursor.execute(MERGE_SQL, {
                "ref": dataset.ref,
                "total_bytes": dataset.total_bytes,
                "last_updated": dataset.last_updated.isoformat()
            })
            logger.debug(f"Upserted: {dataset.ref}")
            new_records += 1

        conn.commit()
        logger.info(f"Run complete. {new_records} records upserted.")

    except Exception as e:
        conn.rollback()
        logger.error(f"Run failed, transaction rolled back: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


# Initialize Kaggle API once
try:
    api = KaggleApi()
    api.authenticate()
    logger.info("Kaggle API authenticated successfully.")
except Exception as e:
    logger.error(f"Authentication failed: {e}")
    raise

run("sentiment")
