"""
API is paginated
API returns duplicates across pages
Keep the latest record per property using updated_at
Retry 3 times on 500/502/503
Return final deduplicated list
large number of properties, so use generator to yield results
"""

from concurrent.futures import process

import requests
import logging

from traitlets import Any

logger = logging.getLogger(__name__)

# implement the get_properties function to retrieve all properties from the API, deduplicate them, and return the final list
import requests
import logging

logger = logging.getLogger(__name__)


import time
import requests

# implement the get_properties function to retrieve all properties from the API, deduplicate them, and return the final list
def iter_properties(url):
    page = 1
    max_tries = 3

    while page:
        for attempt in range(max_tries):
            try:
                response = requests.get(
                    url,
                    params={"page": page},
                    timeout=30
                )

                response.raise_for_status()
                payload = response.json()

                yield from payload.get("data", [])

                page = payload.get("next_page")
                break
            except requests.RequestException:
                if attempt == max_tries - 1:
                    raise
                time.sleep(2 ** attempt)

def transform_property(record):
    # transform the record as needed
    return record

def process(record: Any) -> None
    transformed = transform_property(record)
    snowflake_writer.write(transformed)

def get_properties(url: str = "https://api.company.com/properties"):
    for record in iter_properties(url=url):
        process(record)
