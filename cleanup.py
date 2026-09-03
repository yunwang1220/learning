from collections import Counter


def get_invalid_records(events: list) -> list:
    return [e for e in events if e["property_id"] is None]


def get_valid_records(events: list) -> list:
    valid_raw = [e for e in events if e["property_id"] is not None]
    seen = set()
    deduped = []
    for e in valid_raw:
        key = (e["property_id"], e["event"], e["user"])
        if key not in seen:
            seen.add(key)
            deduped.append(e)
    return deduped


def aggregate(valid_records: list) -> list:
    counts = Counter((e["property_id"], e["event"]) for e in valid_records)
    return [{"property_id": pid, "event": event, "count": count}
            for (pid, event), count in counts.items()]


def build_quality_report(events: list, valid_records: list, invalid_records: list, results: list) -> dict:
    valid_raw_count = len([e for e in events if e["property_id"] is not None])
    return {
        "total_input": len(events),
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "duplicates_removed": valid_raw_count - len(valid_records),
        "unique_property_events": len(results)
    }


if __name__ == "__main__":
    events = [
        {"property_id": 1, "event": "view", "user": "A"},
        {"property_id": 1, "event": "view", "user": "C"},
        {"property_id": 1, "event": "view", "user": "A"},
        {"property_id": 1, "event": "save", "user": "C"},
        {"property_id": 2, "event": "save", "user": "B"},
        {"property_id": None, "event": "view", "user": "C"},
    ]

    invalid_records = get_invalid_records(events)
    valid_records = get_valid_records(events)
    results = aggregate(valid_records)
    quality_report = build_quality_report(events, valid_records, invalid_records, results)

    print("Valid records:  ", valid_records)
    print("Invalid records:", invalid_records)
    print("Results:        ", results)
    print("Quality report: ", quality_report)
