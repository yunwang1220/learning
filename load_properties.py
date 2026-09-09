from datetime import datetime
from typing import List, Dict, Any


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