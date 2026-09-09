from collections import Counter
from typing import List, Dict, Any
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)


def get_all_properties() -> List[Dict[str, Any]]:
    page = 1
    properties = []

    while page:
        try:
            response = requests.get(
                "https://api.company.com/properties",
                params={"page": page},
                timeout=30
            )
            # check for HTTP errors and raise an exception if any occurred
            response.raise_for_status()
            """
            {
                "data": [
                    {"id": 1},
                    {"id": 2}
                ],
                "next_page": 2
            }
            """
            payload = response.json()
            # extend the properties list with the data from the current page .get(key, default)
            properties.extend(payload.get("data", []))
            page = payload.get("next_page")

        except requests.RequestException as e:
            logger.error(
                "Failed to retrieve page %s: %s",
                page,
                str(e)
            )
            raise
    # example of the returned properties list looks like this:
    # [
    #    {"id": 1},
    #    {"id": 2}
    # ]
    return properties

def load_properties(
    properties: List[Dict[str, Any]],
    last_loaded_at: datetime
) -> List[Dict[str, Any]]:
    return [
        property_record
        for property_record in properties
        if datetime.fromisoformat(
            property_record["updated_at"]
        ) >= last_loaded_at
    ]

records = get_all_properties()
last_loaded_at = datetime.fromisoformat("2026-09-08T00:00:00")

load_properties(records, last_loaded_at)
