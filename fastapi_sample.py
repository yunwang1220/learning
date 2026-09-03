import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import snowflake.connector

load_dotenv()

conn = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to Snowflake once on startup (SSO browser window opens here)
    global conn
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="externalbrowser",
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"]
    )
    yield
    conn.close()


app = FastAPI(lifespan=lifespan)


class Dataset(BaseModel):
    ref: str
    total_bytes: int
    last_updated: str


def row_to_dict(row):
    return {"ref": row[0], "total_bytes": row[1], "last_updated": str(row[2])}


@app.get("/")
def read_root():
    return {"message": "Kaggle Dataset API"}


@app.get("/datasets")
def list_datasets():
    cursor = conn.cursor()
    cursor.execute("SELECT ref, total_bytes, last_updated FROM LF_DEV.TMP.KAGGLE ORDER BY last_updated ASC")
    return [row_to_dict(row) for row in cursor.fetchall()]


@app.get("/datasets/{ref:path}")
def get_dataset(ref: str):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ref, total_bytes, last_updated FROM LF_DEV.TMP.KAGGLE WHERE ref = %s",
        (ref,)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return row_to_dict(row)


@app.post("/datasets")
def create_dataset(dataset: Dataset):
    cursor = conn.cursor()
    cursor.execute("SELECT ref FROM LF_DEV.TMP.KAGGLE WHERE ref = %s", (dataset.ref,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Dataset already exists")
    cursor.execute(
        "INSERT INTO LF_DEV.TMP.KAGGLE (ref, total_bytes, last_updated) VALUES (%s, %s, %s::TIMESTAMP_NTZ)",
        (dataset.ref, dataset.total_bytes, dataset.last_updated)
    )
    conn.commit()
    return dataset


@app.put("/datasets/{ref:path}")
def update_dataset(ref: str, dataset: Dataset):
    cursor = conn.cursor()
    cursor.execute("SELECT ref FROM LF_DEV.TMP.KAGGLE WHERE ref = %s", (ref,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Dataset not found")
    cursor.execute(
        "UPDATE LF_DEV.TMP.KAGGLE SET total_bytes = %s, last_updated = %s::TIMESTAMP_NTZ WHERE ref = %s",
        (dataset.total_bytes, dataset.last_updated, ref)
    )
    conn.commit()
    return dataset


@app.delete("/datasets/{ref:path}")
def delete_dataset(ref: str):
    cursor = conn.cursor()
    cursor.execute("SELECT ref FROM LF_DEV.TMP.KAGGLE WHERE ref = %s", (ref,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Dataset not found")
    cursor.execute("DELETE FROM LF_DEV.TMP.KAGGLE WHERE ref = %s", (ref,))
    conn.commit()
    return {"message": f"{ref} deleted"}
