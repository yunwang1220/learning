"""
{
    "property_id": 1001,
    "suburb": "Richmond",
    "price": 1200000
}
"""

"""
{
    "property_id": 1001,
    "suburb": "RICHMOND",
    "price": 1200000,
    "loaded_at": "2026-09-09T12:00:00"
}
"""

from datetime import datetime

import logging

logger = logging.getLogger(__name__)

def transform_property(records):
    properties = []
    invalid_records = []

    loaded_at = datetime.now().isoformat()

    # loop through the records and transform each one
    for record in records:
        # add try/except block to catch any exceptions and log them
        try:
            # add validations
            # check if property_id is present and is an integer
            if "property_id" not in record or record["property_id"] is None or not isinstance(record["property_id"], int):
                raise ValueError("Invalid property_id in record")
            # check if price is present and is a positive number
            if "price" not in record or record["price"] is None or not isinstance(record["price"], (int, float)) or record["price"] <= 0:
                raise ValueError("Invalid price in record")
            
            property_id = record["property_id"]
            # if suburb is not present, use 'UNKNOWN'
            suburb = record.get("suburb", "UNKNOWN").upper()
            price = record["price"]

            transformed_record = {
                "property_id": property_id,
                "suburb": suburb,
                "price": price,
                "loaded_at": loaded_at
            }
            properties.append(transformed_record)

        except ValueError as e:
            # log warning for invalid records and continue processing the next record
            logger.warning(f"Skipping invalid record {record}: {e}")
            invalid_records.append(record)
            continue

    return properties, invalid_records
