import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator, Field
import snowflake.connector

from db import get_snowflake_connection, TABLE

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

conn = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global conn
    logger.info("Connecting to Snowflake...")
    conn = get_snowflake_connection()
    logger.info("Snowflake connection established.")
    yield
    conn.close()
    logger.info("Snowflake connection closed.")


app = FastAPI(lifespan=lifespan)


class Dataset(BaseModel):
    ref: str = Field(..., min_length=3, description="Kaggle dataset ref in format owner/dataset-name")
    dataset_id: int = Field(..., ge=0, description="Kaggle dataset ID")
    total_bytes: int = Field(..., ge=0, description="Total size in bytes, must be >= 0")
    last_updated: str = Field(..., description="ISO 8601 datetime string e.g. 2024-01-01T00:00:00")

    @field_validator("ref")
    @classmethod
    def ref_must_contain_slash(cls, v):
        if "/" not in v:
            raise ValueError("ref must be in format owner/dataset-name")
        return v.strip()

    @field_validator("last_updated")
    @classmethod
    def last_updated_must_be_valid_datetime(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("last_updated must be a valid ISO 8601 datetime e.g. 2024-01-01T00:00:00")
        return v


def row_to_dict(row):
    return {"ref": row[0], "dataset_id": row[1], "total_bytes": row[2], "last_updated": str(row[3])}


def get_cursor():
    """Return a new cursor for each request to avoid thread-safety issues."""
    return conn.cursor()


@app.get("/")
def read_root():
    return {"message": "Kaggle Dataset API"}


@app.get("/datasets")
def list_datasets():
    cursor = get_cursor()
    try:
        cursor.execute(f"SELECT ref, dataset_id, total_bytes, last_updated FROM {TABLE} ORDER BY last_updated ASC")
        return [row_to_dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve datasets")
    finally:
        cursor.close()


@app.get("/datasets/{ref:path}")
def get_dataset(ref: str):
    cursor = get_cursor()
    try:
        cursor.execute(f"SELECT ref, dataset_id, total_bytes, last_updated FROM {TABLE} WHERE ref = %s", (ref,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Dataset not found")
        logger.info(f"Fetched dataset: {ref}")
        return row_to_dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset {ref!r}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve dataset")
    finally:
        cursor.close()


@app.post("/datasets", status_code=201)
def create_dataset(dataset: Dataset):
    cursor = get_cursor()
    try:
        cursor.execute(f"SELECT ref FROM {TABLE} WHERE ref = %s", (dataset.ref,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Dataset already exists")
        cursor.execute(
            f"INSERT INTO {TABLE} (ref, dataset_id, total_bytes, last_updated) VALUES (%s, %s, %s, %s::TIMESTAMP_NTZ)",
            (dataset.ref, dataset.dataset_id, dataset.total_bytes, dataset.last_updated)
        )
        conn.commit()
        logger.info(f"Created dataset: {dataset.ref}")
        return dataset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create dataset {dataset.ref!r}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create dataset")
    finally:
        cursor.close()


@app.put("/datasets/{ref:path}")
def update_dataset(ref: str, dataset: Dataset):
    cursor = get_cursor()
    try:
        cursor.execute(f"SELECT ref FROM {TABLE} WHERE ref = %s", (ref,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Dataset not found")
        cursor.execute(
            f"UPDATE {TABLE} SET dataset_id = %s, total_bytes = %s, last_updated = %s::TIMESTAMP_NTZ WHERE ref = %s",
            (dataset.dataset_id, dataset.total_bytes, dataset.last_updated, ref)
        )
        conn.commit()
        logger.info(f"Updated dataset: {ref}")
        return dataset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update dataset {ref!r}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update dataset")
    finally:
        cursor.close()


@app.delete("/datasets/{ref:path}")
def delete_dataset(ref: str):
    cursor = get_cursor()
    try:
        cursor.execute(f"SELECT ref FROM {TABLE} WHERE ref = %s", (ref,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Dataset not found")
        cursor.execute(f"DELETE FROM {TABLE} WHERE ref = %s", (ref,))
        conn.commit()
        logger.info(f"Deleted dataset: {ref}")
        return {"message": f"{ref} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset {ref!r}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete dataset")
    finally:
        cursor.close()
