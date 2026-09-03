from collections import Counter

events = [
    {"property_id": 1, "event": "view", "user": "A"},
    {"property_id": 1, "event": "view", "user": "C"},
    {"property_id": 1, "event": "view", "user": "A"},
    {"property_id": 1, "event": "save", "user": "C"},
    {"property_id": 2, "event": "save", "user": "B"},
    {"property_id": None, "event": "view", "user": "C"},
]

# Filter invalid then deduplicate by (property_id, event, user)
# Removes duplicates and Removes invalid records by using set and if condition
valid = {(e["property_id"], e["event"], e["user"])
         for e in events if e["property_id"] is not None} #set{} deduplicate but not ordered

# Count unique occurrences by (property_id, event)
# Returns counts by (property_id, event)
counts = Counter((pid, event) for pid, event, user in valid)

results = [{"property_id": pid, "event": event, "count": count}
           for (pid, event), count in counts.items()]

print(results)
