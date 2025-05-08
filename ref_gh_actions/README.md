# Reference GitHub Actions Templates

This directory contains reference GitHub Actions workflow templates for validating MCP server implementations. These templates are meant to be copied into your own MCP server repository and customized as needed.

## Available Templates

- `stdio-validation.yml` - Template for validating STDIO-based MCP servers
- `http-validation.yml` - Template for validating HTTP-based MCP servers

## Features

- Automated validation on pull requests
- Manual trigger option
- Configurable protocol versions
- Detailed test reporting
- PR comment summaries
- Artifact storage for test reports
- Error handling and server health checks
- Environment variable support

## Usage

1. Copy the relevant template(s) to your server's `.github/workflows/` directory
2. Update the server path/command to point to your implementation
3. Configure environment variables if needed (API keys, ports, etc.)
4. Adjust timeouts and other parameters as needed
5. Commit and push to enable automated validation

## Template Customization

### Common Settings
- Protocol versions in matrix strategy
- Python version
- Test timeouts
- Environment variables

### STDIO-specific
- Server command and path
- Test mode options
- Tool selection

### HTTP-specific
- Server port
- Health check settings
- Startup retry settings

## Best Practices

1. Always use environment variables or secrets for sensitive data
2. Set appropriate timeouts based on your server's needs
3. Include proper error handling and cleanup
4. Use the health check endpoint for HTTP servers
5. Keep test artifacts for debugging

See the comments in each template file for detailed customization instructions. 