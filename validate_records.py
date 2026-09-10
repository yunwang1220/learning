"""
records = [
    {
        "property_id": 1,
        "suburb": "Richmond"
    },
    {
        "property_id": None,
        "suburb": "Hawthorn"
    },
    {
        "property_id": 2,
        "suburb": None
    }
]

expected output:
{
    "total": 3,
    "valid": 1,
    "invalid": 2
}
"""
import logging

logger = logging.getLogger(__name__)

# validate that all records have a property_id and suburb
records = [
    {
        "property_id": 1,
        "suburb": "Richmond"
    },
    {
        "property_id": None,
        "suburb": "Hawthorn"
    },
    {
        "property_id": 2,
        "suburb": None
    }
]

# improve the validate_records to facilitate a large number of records by using generator to yield results
def validate_records(records):
    """
    Validate records lazily and yield each validation decision as a generator.
    After the stream is exhausted, a final quality_report is yielded.
    """
    total = 0
    valid = 0
    invalid = 0

    for record in records:
        total += 1
        try:
            property_id = record.get("property_id")
            suburb = record.get("suburb")

            if not isinstance(property_id, int) or isinstance(property_id, bool) or property_id is None:
                raise ValueError(f"Invalid property_id: {property_id}")
            if not isinstance(suburb, str) or suburb is None:
                raise ValueError(f"Invalid suburb: {suburb}")

            valid += 1
            yield {
                "type": "record",
                "record": record,
                "valid": True,
            }
        except ValueError as e:
            logger.warning(e)
            invalid += 1
            yield {
                "type": "record",
                "record": record,
                "valid": False,
                "error": str(e),
            }

    quality_report = {
        "type": "summary",
        "total": total,
        "valid": valid,
        "invalid": invalid,
    }

    logger.info(f"Validation results: {quality_report}")
    yield {
        "type": "summary",
        "summary": quality_report
    }

# Example usage:
def process_validation_results(records):
    for result in validate_records(records):
        if result["type"] == "record":
            if result.get("valid"):
                load_to_snowflake(result["record"])
            else:
                write_to_quarantine(result)  # Placeholder for actual database writing logic
        elif result["type"] == "summary":
            logger.info(f"Validation summary: {result['summary']}")
