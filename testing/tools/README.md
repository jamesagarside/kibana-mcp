# Kibana MCP Tool Tests

This directory contains tests for the Kibana MCP tools, organized by category.

## Directory Structure

- `alerts/`: Tests for alert management tools
- `rules/`: Tests for rule management tools
- `exceptions/`: Tests for exception management tools
- `utils/`: Test utilities

## Running the Tests

To run all tests:

```bash
cd /Users/jamesgarside/Github/jamesagarside/kibana-mcp
PYTHONPATH=/Users/jamesgarside/Github/jamesagarside/kibana-mcp/src pytest -xvs testing/tools/test_all.py
```

To run tests for a specific category:

```bash
# For alert tools
PYTHONPATH=/Users/jamesgarside/Github/jamesagarside/kibana-mcp/src pytest -xvs testing/tools/alerts/test_alert_tools.py

# For rule tools
PYTHONPATH=/Users/jamesgarside/Github/jamesagarside/kibana-mcp/src pytest -xvs testing/tools/rules/test_rule_tools.py

# For exception tools
PYTHONPATH=/Users/jamesgarside/Github/jamesagarside/kibana-mcp/src pytest -xvs testing/tools/exceptions/test_exception_tools.py
```
