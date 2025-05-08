# MCP Protocol Validator

A testing suite and reference implementation for the [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol).

## Summary

The MCP Protocol Validator provides a comprehensive environment for testing and validating MCP server implementations. It includes reference implementations and a testing framework to ensure compliance with the MCP specification.


## STDIO Compliance Testing

The validator includes a comprehensive testing suite for STDIO-based MCP servers.

### Running STDIO Tests

```bash
# Run compliance tests for the STDIO server
python -m mcp_testing.scripts.compliance_report --server-command "python ref_stdio_server/stdio_server_2025_03_26.py" --protocol-version 2025-03-26
```

### STDIO Test Coverage

The STDIO compliance tests verify:
1. Protocol Initialization
2. Tools Functionality
   - Basic tools (echo, add)
   - Async tools (sleep) for 2025-03-26 version
3. Error Handling
4. Protocol Version Negotiation

### Testing Different STDIO Server Types

The validator supports testing any STDIO-based MCP server, whether it's run directly from a command or installed via pip. Here's how to test different types of servers:

#### Direct Command Testing

For servers that run directly from a Python file or command:

```bash
# Test a local Python file
python -m mcp_testing.scripts.compliance_report --server-command "python path/to/your/server.py" --protocol-version 2025-03-26

# Test with specific timeouts
python -m mcp_testing.scripts.compliance_report --server-command "python path/to/server.py" --protocol-version 2025-03-26 --test-timeout 30 --tools-timeout 15

# Focus on tools testing with dynamic discovery
python -m mcp_testing.scripts.compliance_report --server-command "python path/to/server.py" --protocol-version 2025-03-26 --test-mode tools --dynamic-only
```

#### Testing Pip-Installed Servers

For servers installed via pip (like `mcp-server-fetch`):

```bash
<<<<<<< Updated upstream
# Ensure you're in the correct virtual environment
source .venv/bin/activate
=======
# Test STDIO server with core protocol features only (most reliable option)
python -m mcp_testing.scripts.compliance_report --server-command "./minimal_mcp_server/minimal_mcp_server.py" --protocol-version 2025-03-26 --test-mode core

# Test STDIO server (skip async tests to avoid potential hanging issues)
# Note: The standalone test scripts above provide better test coverage
python -m mcp_testing.scripts.compliance_report --server-command "./minimal_mcp_server/minimal_mcp_server.py" --protocol-version 2025-03-26 --skip-async
>>>>>>> Stashed changes

# Install the server and dependencies
pip install your-mcp-server  # Replace with actual package name

<<<<<<< Updated upstream
# Run compliance tests
python -m mcp_testing.scripts.compliance_report --server-command "python -m your_server_module" --protocol-version 2024-11-05

# Run tools-only tests
python -m mcp_testing.scripts.compliance_report --server-command "python -m your_server_module" --protocol-version 2024-11-05 --test-mode tools

# example brave search server
BRAVE_API_KEY=api-key python -m mcp_testing.scripts.compliance_report --server-command "npx -y @modelcontextprotocol/server-brave-search" --protocol-version 2024-11-05 
```

#### Test Configuration Options
=======
# Generate reports
python -m mcp_testing.scripts.compliance_report --server-command "./minimal_mcp_server/minimal_mcp_server.py" --output-dir "./reports" --test-mode core
python -m mcp_testing.scripts.http_test --server-url http://localhost:8000/mcp --output-dir "./reports"
```

> **Note:** The compliance report tool may hang when testing async features or tool functionality with the STDIO server. 
> For the most reliable testing, use the `--test-mode core` option or use the dedicated test scripts (`test_minimal_server.py --full`) 
> which provide complete coverage including async features and tools.

## Reference Implementations
>>>>>>> Stashed changes

Common options for both types:

- `--test-mode tools`: Focus on testing tool functionality
- `--dynamic-only`: Automatically discover and test available tools
- `--test-timeout 30`: Set timeout for regular tests (seconds)
- `--tools-timeout 15`: Set timeout for tool-specific tests (seconds)
- `--required-tools tool1,tool2`: Specify required tools to test
- `--skip-tests test1,test2`: Skip specific tests
- `--skip-async`: Skip async tool testing

Note: Tool-related tests that timeout are treated as non-critical, allowing testing to continue.

### Test Reports

Each test run generates a detailed report containing:
- Server information (command, protocol version)
- Test execution timestamp
- Test duration
- Success rate
- Detailed results for each test case
- Server capabilities
- Session information


### Running Tests

You can run different types of tests using module-style commands:

```bash
# Basic interaction test
python -m mcp_testing.scripts.basic_interaction --server-command "python -m mcp_server_fetch" --protocol-version 2024-11-05

# Compliance tests with tools-only mode
python -m mcp_testing.scripts.compliance_report --server-command "python -m mcp_server_fetch" --protocol-version 2024-11-05 --test-mode tools

<<<<<<< Updated upstream
# Set custom timeouts for tools tests vs. other tests
python -m mcp_testing.scripts.compliance_report --server-command "python -m mcp_server_fetch" --protocol-version 2024-11-05 --test-timeout 30 --tools-timeout 15
=======
# Test only specific functionality
python -m mcp_testing.scripts.compliance_report --server-command "/path/to/server" --test-mode tools

# Skip async tests if experiencing hanging issues
python -m mcp_testing.scripts.compliance_report --server-command "/path/to/server" --skip-async

# HTTP debug output
python -m mcp_testing.scripts.http_test --server-url http://localhost:8000/mcp --debug
>>>>>>> Stashed changes
```

Note: Tool-related tests that timeout are treated as non-critical, allowing testing to continue.

## HTTP Compliance Testing

The validator includes a basic compliance testing suite for HTTP-based MCP servers.

### Running HTTP Tests

```bash
# Start the reference HTTP server (runs on port 8088)
python ref_http_server/reference_mcp_server.py

# Run compliance tests and generate a detailed report
python -m mcp_testing.scripts.http_compliance_test --output-dir reports
```

### HTTP Test Coverage

The HTTP compliance test suite verifies:

1. Protocol Initialization
2. Tools Functionality
3. Error Handling
4. Batch Request Processing
5. Session Management
6. Protocol Negotiation
7. Ping Utility


## Testing Scripts Overview

The following scripts are available in `mcp_testing/scripts/`:

### Active and Maintained
- `http_compliance_test.py`: Primary script for HTTP server testing (7/7 tests passing)
- `compliance_report.py`: Primary script for STDIO server testing (36/37 tests passing)

### Supporting Scripts mixed working/in progress
- `basic_interaction.py`: Simple tool for testing basic server functionality
- `http_test.py`: Lower-level HTTP testing utilities
- `http_compliance.py`: Core HTTP compliance testing logic
- `http_compliance_report.py`: Report generation for HTTP tests
- `run_stdio_tests.py`: Lower-level STDIO testing utilities
- `session_test.py`: Session management testing utilities

## License

SPDX-License-Identifier: AGPL-3.0-or-later
Copyright (c) 2025 Scott Wilcox
