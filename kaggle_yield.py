import logging
import os
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import KaggleApi
import requests

from db import get_snowflake_connection, TABLE

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
LOOKBACK_HOURS = 24
PAGE_LIMIT = 11
MAX_RETRIES = 3
RETRY_BACKOFF = 2
RATE_LIMIT_WAIT = 60
COMMIT_BATCH_SIZE = 50

MERGE_SQL = f"""
MERGE INTO {TABLE} AS target
USING (SELECT %(ref)s AS ref, %(dataset_id)s AS dataset_id, %(total_bytes)s AS total_bytes, %(last_updated)s::TIMESTAMP_NTZ AS last_updated) AS source
ON target.ref = source.ref
WHEN MATCHED AND source.last_updated > target.last_updated THEN
    UPDATE SET dataset_id = source.dataset_id, total_bytes = source.total_bytes, last_updated = source.last_updated
WHEN NOT MATCHED THEN
    INSERT (ref, dataset_id, total_bytes, last_updated) VALUES (source.ref, source.dataset_id, source.total_bytes, source.last_updated)
"""



def load_checkpoint(cursor) -> datetime | None:
    """Derive checkpoint from MAX(last_updated) in Snowflake."""
    cursor.execute(f"SELECT MAX(last_updated) FROM {TABLE}")
    row = cursor.fetchone()
    checkpoint = row[0] if row else None
    if checkpoint:
        checkpoint = checkpoint - timedelta(hours=LOOKBACK_HOURS)
        logger.info(f"Checkpoint (with {LOOKBACK_HOURS}hr lookback): {checkpoint}")
    else:
        logger.info("No checkpoint found, running full load.")
    return checkpoint




def fetch_page_with_retry(api: KaggleApi, search_term: str, page: int) -> list:
    """Fetch a single page with error-specific handling and exponential backoff with jitter."""
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return api.dataset_list(search=search_term, page=page, sort_by='updated')

        except requests.exceptions.HTTPError as e:
            last_error = e
            status = e.response.status_code if e.response is not None else None

            if status == 401:
                logger.error("Authentication failed (401). Check your Kaggle API key.")
                raise

            elif status == 403:
                logger.error(f"Access forbidden (403) on page {page}. Insufficient permissions.")
                raise

            elif status == 404:
                logger.warning(f"Page {page} not found (404), stopping pagination.")
                return []

            elif status == 429:
                wait = int(e.response.headers.get("Retry-After", RATE_LIMIT_WAIT))
                logger.warning(f"Rate limited (429). Waiting {wait}s as advised by API...")
                time.sleep(wait)

            elif status in (500, 502, 503):
                wait = (RETRY_BACKOFF ** attempt) + random.uniform(0, 1)
                logger.warning(f"Server error ({status}) on page {page}, attempt {attempt}. Retrying in {wait:.1f}s...")
                time.sleep(wait)

            else:
                logger.error(f"Unexpected HTTP error ({status}) on page {page}: {e}")
                raise

        except requests.exceptions.Timeout as e:
            last_error = e
            wait = (RETRY_BACKOFF ** attempt) + random.uniform(0, 1)
            logger.warning(f"Request timed out on page {page}, attempt {attempt}. Retrying in {wait:.1f}s...")
            time.sleep(wait)

        except requests.exceptions.ConnectionError as e:
            last_error = e
            wait = (RETRY_BACKOFF ** attempt) + random.uniform(0, 1)
            logger.warning(f"Connection error on page {page}, attempt {attempt}. Retrying in {wait:.1f}s...")
            time.sleep(wait)

    logger.error(f"Page {page} failed after {MAX_RETRIES} attempts, giving up.")
    raise last_error


def yield_kaggle_datasets(api: KaggleApi, search_term: str):
    """Yields individual datasets incrementally from Kaggle, page by page."""
    page = 1
    total_yielded = 0

    while True:
        logger.info(f"Fetching page {page}/{PAGE_LIMIT} for search term: '{search_term}'")
        batch = fetch_page_with_retry(api, search_term, page)

        if not batch:
            logger.info(f"No more datasets on page {page}, pagination complete.")
            break

        batch_size = len(batch)
        yield from batch
        total_yielded += batch_size
        logger.info(f"Page {page}: {batch_size} datasets yielded (total so far: {total_yielded})")

        if batch_size < 20:
            logger.info("Partial page received, pagination complete.")
            break

        if page >= PAGE_LIMIT:
            logger.warning(f"Reached page limit ({PAGE_LIMIT}). Some results may be truncated.")
            break

        page += 1

    logger.info(f"Pagination finished. Total datasets yielded: {total_yielded}")


def validate_dataset(dataset) -> str | None:
    """Validates a Kaggle dataset record. Returns error message or None if valid."""
    if not dataset.ref or "/" not in dataset.ref:
        return f"invalid ref: {dataset.ref!r}"
    if dataset.id is None:
        return "missing dataset_id"
    if dataset.total_bytes is None or dataset.total_bytes < 0:
        return f"invalid total_bytes: {dataset.total_bytes!r}"
    if dataset.last_updated is None:
        return "missing last_updated"
    return None


def run(api: KaggleApi, search_term: str) -> None:
    conn = get_snowflake_connection()
    cursor = conn.cursor()

    try:
        checkpoint = load_checkpoint(cursor)
        new_records = 0
        skipped_records = 0

        for dataset in yield_kaggle_datasets(api, search_term):
            if checkpoint and dataset.last_updated <= checkpoint:
                logger.debug(f"Skipping {dataset.ref}, not updated since checkpoint.")
                continue

            error = validate_dataset(dataset)
            if error:
                logger.warning(f"Skipping invalid record {dataset.ref!r}: {error}")
                skipped_records += 1
                continue

            try:
                cursor.execute(MERGE_SQL, {
                    "ref": dataset.ref,
                    "dataset_id": dataset.id,
                    "total_bytes": dataset.total_bytes,
                    "last_updated": dataset.last_updated.isoformat()
                })
                new_records += 1
            except Exception as e:
                logger.warning(f"Skipping {dataset.ref!r} due to upsert error: {e}")
                skipped_records += 1
                continue

            if new_records % COMMIT_BATCH_SIZE == 0:
                conn.commit()
                logger.info(f"Committed {new_records} records so far...")

        conn.commit()
        logger.info(f"Run complete. {new_records} upserted, {skipped_records} skipped.")

    except Exception as e:
        logger.error(f"Run failed: {e}", exc_info=True)
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    try:
        api = KaggleApi()
        api.authenticate()
        logger.info("Kaggle API authenticated successfully.")
        run(api, "sentiment")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise
