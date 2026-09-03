# Python Built-in Collection Data Types

| Type | Syntax | Ordered | Duplicates | Mutable | Key-Value | General Use |
|------|--------|---------|------------|---------|-----------|-------------|
| list | `[1, 2, 3]` | Yes | Yes | Yes | No | Storing rows of data, iterating over records, building result sets |
| tuple | `(1, 2, 3)` | Yes | Yes | No | No | Representing a single immutable row or composite key (e.g. `(property_id, event)`) |
| set | `{1, 2, 3}` | No | No | Yes | No | Deduplicating records, membership checks (e.g. seen keys, valid IDs) |
| dict | `{"a": 1}` | Yes | No (keys) | Yes | Yes | Grouping and aggregating data by key (e.g. counts per property, lookup tables) |
