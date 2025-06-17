# Saved Objects Tools Testing

This directory contains tests for the Kibana Saved Objects management tools.

## Test Structure

The tests follow the same pattern as other tool categories:

1. Each saved object tool function is tested for both successful and error cases
2. HTTP responses are mocked using AsyncMock
3. Assertions verify proper handling of requests and responses

## Running Tests

To run only the saved objects tool tests:

```bash
# From project root
PYTHONPATH=/path/to/kibana-mcp/src pytest -xvs testing/tools/saved_objects/test_saved_objects.py
```

To run all tests including saved objects tools:

```bash
# From project root
PYTHONPATH=/path/to/kibana-mcp/src pytest -xvs testing/tools/test_all.py
```

## Test Coverage

The tests cover the following saved objects tools:

- `find_objects`: Searching for saved objects by type and other criteria
- `get_object`: Retrieving a single saved object
- `bulk_get_objects`: Retrieving multiple saved objects in bulk
- `create_object`: Creating new saved objects
- `update_object`: Updating existing saved objects
- `delete_object`: Deleting saved objects
- `export_objects`: Exporting saved objects (returns NDJSON)
- `import_objects`: Importing saved objects from NDJSON

## Integration with Main Test Suite

These tests are automatically included when running the full test suite through `test_all.py`.
