import logging
import time
from typing import Dict, Any

from pendulum import datetime
import requests

logger = logging.getLogger(__name__)


def get_property(property_id: int) -> Dict[str, Any]:
    url = f"https://api.company.com/property/{property_id}"

    max_retries = 3
    base_delay = 1

    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                timeout=30
            )

            response.raise_for_status()

            return response.json()

        except requests.HTTPError as e:
            status_code = e.response.status_code

            if status_code not in (500, 502, 503, 504):
                logger.error(
                    "Non-retryable error for property %s: %s",
                    property_id,
                    status_code,
                )
                raise

            if attempt == max_retries - 1:
                logger.error(
                    "Max retries reached for property %s",
                    property_id,
                )
                raise

            delay = base_delay * (2 ** attempt)

            logger.warning(
                "Attempt %s failed for property %s with status %s. Retrying in %s seconds.",
                attempt + 1,
                property_id,
                status_code,
                delay,
            )

            time.sleep(delay)

        except requests.RequestException as e:
            logger.error(
                "Request failed for property %s: %s",
                property_id,
                str(e),
            )

            if attempt == max_retries - 1:
                raise

            delay = base_delay * (2 ** attempt)
            time.sleep(delay)

    raise RuntimeError("Unexpected retry failure")

# GET /properties?updated_after=2026-09-08T00:00:00
def load_properties(
    last_loaded_at: datetime
) -> list[dict]:

    response = requests.get(
        "https://api.company.com/properties"ams={
            "updated_after":
                last_loaded_at.isoformat()
        },
        timeout=30
    )

    response.raise_for_status()
    return response.json()["data"]