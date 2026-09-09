"""
records = [
    {
        "property_id": 1,
        "updated_at": "2026-09-08T10:00:00"
    },
    {
        "property_id": 1,
        "updated_at": "2026-09-08T11:00:00"
    },
    {
        "property_id": 2,
        "updated_at": "2026-09-08T10:00:00"
    }
]
"""

"""
[
    {
        "property_id": 1,
        "updated_at": "2026-09-08T11:00:00"
    },
    {
        "property_id": 2,
        "updated_at": "2026-09-08T10:00:00"
    }
]
"""

def get_latest_properties(records):
    latest_records = {}
    for record in records:
        property_id = record["property_id"]
        updated_at = record["updated_at"]
        if property_id not in latest_records or updated_at > latest_records[property_id]["updated_at"]:
            latest_records[property_id] = record
    return list(latest_records.values())