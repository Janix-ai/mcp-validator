# GitHub Actions for MCP Protocol Validator

This guide explains how to set up GitHub Actions to automate compliance testing for MCP server implementations using your existing MCP Protocol Validator repository.

## Overview

These GitHub Actions automatically run MCP compliance tests on pull requests, helping ensure that your MCP implementations remain compliant with the protocol specification as you make changes.

## Repository Structure

Your existing MCP Validator repository already contains the necessary testing frameworks:

```
mcp-validator/
├── mcp_testing/
│   └── scripts/
│       ├── compliance_report.py      # For STDIO server testing
│       ├── http_compliance_test.py   # For HTTP server testing
│       └── ...
├── ref_stdio_server/
│   └── stdio_server_2025_03_26.py
├── ref_http_server/
│   └── reference_mcp_server.py
└── README.md
```

The GitHub Actions will leverage these existing scripts to run automated tests on your pull requests.

## Integration Steps

### 1. Create GitHub Actions Directory

First, create a `.github/workflows` directory in the root of your repository:

```bash
mkdir -p .github/workflows
```

### 2. Add STDIO Validation Workflow

Create a file at `.github/workflows/mcp-stdio-validation.yml` with the workflow configuration for STDIO server testing.

### 3. Add HTTP Validation Workflow

Create a file at `.github/workflows/mcp-http-validation.yml` with the workflow configuration for HTTP server testing.

### 4. Commit and Push the Changes

Add the GitHub Actions workflows to your repository:

```bash
git add .github/workflows/mcp-stdio-validation.yml
git add .github/workflows/mcp-http-validation.yml
git commit -m "Add MCP validator GitHub Actions"
git push
```

## Using the GitHub Actions

### Automated Testing on Pull Requests

Once set up, these GitHub Actions will automatically run whenever a pull request is opened against your `main` or `master` branch. The workflow will:

1. Check out your code
2. Set up Python
3. Install dependencies
4. Run the compliance tests
5. Upload the test reports as artifacts
6. Post a summary of the results as a comment on the PR

### Manual Triggering

You can also manually trigger the workflows:

1. Go to the "Actions" tab in your GitHub repository
2. Select either "MCP STDIO Protocol Validation" or "MCP HTTP Protocol Validation"
3. Click "Run workflow" on the right side
4. Select the branch to run the workflow on
5. Click "Run workflow"

## Customizing the Workflows

### Testing Your Own Server Implementation

To test your own server implementation instead of the reference implementations:

1. For STDIO server testing, modify the `--server-command` parameter:
   ```yaml
   --server-command "python path/to/your/stdio_server.py"
   ```

2. For HTTP server testing, modify the server start command:
   ```yaml
   python path/to/your/http_server.py &
   ```

### Testing Multiple Protocol Versions

To test multiple protocol versions, update the matrix configuration:

```yaml
strategy:
  matrix:
    protocol-version: ["2024-11-05", "2025-03-26"]
```

### Adjusting Test Parameters

You can adjust test parameters based on your needs:

```yaml
--test-timeout 60     # Increase timeout for regular tests
--tools-timeout 30    # Increase timeout for tool-specific tests
--test-mode tools     # Focus on testing tool functionality
--dynamic-only        # Automatically discover and test available tools
--required-tools tool1,tool2    # Specify required tools to test
--skip-tests test1,test2        # Skip specific tests
--skip-async          # Skip async tool testing
```

## Accessing Test Results

### PR Comments

After the workflow runs, it will post a comment on the PR with a summary of the test results, including:
- Protocol version tested
- Success rate
- Number of tests run
- Details of any failed tests

### Artifacts

For more detailed results, you can access the test artifacts:

1. Go to the workflow run in the "Actions" tab
2. Scroll down to the "Artifacts" section
3. Click on either "mcp-stdio-reports" or "mcp-http-reports" to download the detailed test reports

## Troubleshooting

### Common Issues

1. **Dependency Errors**: Ensure all required dependencies are specified in your `setup.py` or `requirements.txt` file.

2. **Path Errors**: Verify that the paths to your server implementations are correct.

3. **Permission Issues**: Make sure your server files have executable permissions.

4. **Timeout Errors**: If tests are timing out, increase the timeout values in the workflow configuration.

## Extending the Workflows

As your needs grow, you can extend these workflows to:

1. Test custom MCP tools
2. Compare your implementation against reference implementations
3. Test across multiple environments or configurations
4. Integrate with other CI/CD processes

## Additional Resources

- Refer to the [MCP Protocol Validator documentation](https://github.com/modelcontextprotocol) for details on test scripts and options
- See [GitHub Actions documentation](https://docs.github.com/en/actions) for more information on GitHub Actions features

## License

These GitHub Actions workflows are provided under the same license as the MCP Protocol Validator:
SPDX-License-Identifier: AGPL-3.0-or-later 