# Endpoint Tools Testing

This directory contains tests for the Elastic Security endpoint management and response action tools.

## Test Structure

The tests follow the same pattern as other tool categories:

1. Each endpoint tool function is tested for both successful and error cases
2. HTTP responses are mocked using AsyncMock
3. Assertions verify proper handling of requests and responses

## Running Tests

To run only the endpoint tool tests:

```bash
# From project root
PYTHONPATH=/path/to/kibana-mcp/src pytest -xvs testing/tools/endpoint/test_endpoint_tools.py
```

To run all tests including endpoint tools:

```bash
# From project root
PYTHONPATH=/path/to/kibana-mcp/src pytest -xvs testing/tools/test_all.py
```

## Test Coverage

The tests cover the following endpoint tools:

- `isolate_endpoint`: Network isolation for endpoints
- `unisolate_endpoint`: Releasing endpoints from network isolation
- `run_command_on_endpoint`: Running shell commands on endpoints
- `get_response_actions`: Retrieving all response actions
- `get_response_action_details`: Getting details of specific response actions
- `get_response_action_status`: Checking status of response actions
- `kill_process`: Terminating processes on endpoints
- `suspend_process`: Suspending processes on endpoints
- `scan_endpoint`: Running malware scans on endpoints
- `get_file_info`: Getting metadata for files from endpoints
- `download_file`: Downloading files from endpoints

## End-to-End Testing

For end-to-end testing with actual Fleet Server and Elastic Agent services:

### Automated Setup (Recommended)

Just run the automated setup script which handles everything:

```bash
./testing/start-endpoint-test-env.sh
```

This script will:

1. Start Elasticsearch and Kibana
2. Configure Fleet Server and Agent policies
3. Automatically update docker-compose.yml with the required tokens
4. Start Fleet Server and Elastic Agent

### Manual Setup

If you prefer to control each step:

1. Start the local environment:

   ```bash
   docker-compose -f testing/docker-compose.yml up -d elasticsearch kibana
   ```

2. Run the Fleet setup script (which now automatically updates docker-compose.yml):

   ```bash
   ./testing/setup-fleet.sh
   ```

3. Start Fleet Server:

   ```bash
   docker-compose -f testing/docker-compose.yml up -d fleet-server
   sleep 15  # Wait for Fleet Server to initialize
   ```

4. Start Elastic Agent:

   ```bash
   docker-compose -f testing/docker-compose.yml up -d elastic-agent
   ```

5. Verify in Kibana at http://localhost:5601 under Management > Fleet
