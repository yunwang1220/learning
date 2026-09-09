import requests
from datetime import datetime


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