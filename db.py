import logging
import os
import snowflake.connector

logger = logging.getLogger(__name__)

TABLE = "LF_DEV.TMP.KAGGLE"


def get_snowflake_connection() -> snowflake.connector.SnowflakeConnection:
    try:
        return snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            authenticator="externalbrowser",
            warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
            database=os.environ["SNOWFLAKE_DATABASE"],
            schema=os.environ["SNOWFLAKE_SCHEMA"]
        )
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        raise
    except snowflake.connector.errors.DatabaseError as e:
        logger.error(f"Failed to connect to Snowflake: {e}")
        raise
