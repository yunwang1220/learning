# Python Built-in Collection Data Types

| Type | Syntax | Ordered | Duplicates | Mutable | Key-Value | General Use |
|------|--------|---------|------------|---------|-----------|-------------|
| list | `[1, 2, 3]` | Yes | Yes | Yes | No | Storing rows of data, iterating over records, building result sets |
| tuple | `(1, 2, 3)` | Yes | Yes | No | No | Representing a single immutable row or composite key (e.g. `(property_id, event)`) |
| set | `{1, 2, 3}` | No | No | Yes | No | Deduplicating records, membership checks (e.g. seen keys, valid IDs) |
| dict | `{"a": 1}` | Yes | No (keys) | Yes | Yes | Grouping and aggregating data by key (e.g. counts per property, lookup tables) |

---

# Project Files

## cleanup.py
Removes duplicate and invalid records from an events list, then aggregates event counts per property.
- Filters out records where `property_id` is `None`
- Deduplicates using a set comprehension on `(property_id, event, user)`
- Aggregates using `collections.Counter` to produce `property_id`, `event`, `count`

## kaggle_yield.py
Incremental pipeline that fetches datasets from the Kaggle API and upserts them into `LF_DEV.TMP.KAGGLE`.
- Authenticates with Kaggle via `~/.kaggle/kaggle.json`
- Authenticates with Snowflake via SSO (`externalbrowser`)
- Watermark derived from `MAX(last_updated)` in Snowflake with a 24hr lookback for late arriving data
- Uses `MERGE` for idempotent upserts
- Fetches pages newest-to-oldest, commits per record for resumption on interruption

## fastapi_sample.py
REST API exposing CRUD operations on `LF_DEV.TMP.KAGGLE` using FastAPI and Snowflake.
- Connects to Snowflake once at startup via SSO
- Supports `GET`, `POST`, `PUT`, `DELETE` on `/datasets`
- Handles Kaggle refs with slashes using `{ref:path}`
- Uses parameterised queries to prevent SQL injection

**Run:**
```bash
uvicorn fastapi_sample:app --reload
```
Swagger UI available at `http://localhost:8000/docs`

---

# Setup

## Install dependencies
```bash
pip install kaggle snowflake-connector-python python-dotenv fastapi uvicorn
```

## Configure .env
```
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

SNOWFLAKE_ACCOUNT=linfox-linfox
SNOWFLAKE_USER=your_email
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=LF_DEV
SNOWFLAKE_SCHEMA=TMP
```

