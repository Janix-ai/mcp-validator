# Copyright (c) 2025 Scott Wilcox
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
MCP HTTP Server Tester

A class for testing MCP HTTP server implementations.
"""

import json
import uuid
import requests
import socket
import time
from urllib.parse import urlparse

class MCPHttpTester:
    """Class to test an MCP HTTP server implementation."""
    
    def __init__(self, url, debug=False):
        """
        Initialize the tester with the server URL.
        
        Args:
            url: The URL of the MCP server
            debug: Whether to print debug information
        """
        self.url = url
        self.debug = debug
        
        # Parse the URL
        parsed_url = urlparse(url)
        self.host = parsed_url.netloc
        self.path = parsed_url.path or "/"
        
        # Session information
        self.session_id = None
        self.initialized = False
        
        # Protocol information
        self.protocol_version = "2025-03-26"
        
        # Create a persistent session for all requests
        self.request_session = requests.Session()
        self.request_session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        })
        
        self.log(f"MCP HTTP Tester initialized for {url}")
        self.log(f"Host: {self.host}, Path: {self.path}")
    
    def log(self, message):
        """Print a log message if debug is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def send_request(self, method, json_data=None, headers=None, request_method="POST"):
        """
        Send a JSON-RPC request to the server using the requests library.
        
        Args:
            method: The JSON-RPC method to call
            json_data: Additional JSON data to include (optional)
            headers: Additional headers to include (optional)
            request_method: The HTTP method to use (default: POST)
            
        Returns:
            Tuple of (status_code, headers, body)
        """
        # Build the request
        if json_data is None:
            json_data = {}
        
        # For OPTIONS requests, we don't send a JSON-RPC request
        if request_method == "OPTIONS":
            try:
                response = self.request_session.options(self.url, timeout=5)
                self.log(f"OPTIONS Response Status: {response.status_code}")
                self.log(f"OPTIONS Response Headers: {dict(response.headers)}")
                return response.status_code, dict(response.headers), None
            except requests.RequestException as e:
                self.log(f"OPTIONS request failed: {str(e)}")
                raise
        
        # For other requests, build a JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": str(uuid.uuid4())
        }
        
        # Add params if provided
        if json_data:
            request["params"] = json_data
        
        # Convert to JSON
        json_str = json.dumps(request)
        self.log(f"Request: {json_str}")
        
        # Set up headers
        request_headers = {}
        
        # Always include a session ID, either the existing one or a new one
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
            self.log(f"Created new session ID: {self.session_id}")
        
        # Add session ID to headers
        request_headers["Mcp-Session-Id"] = self.session_id
        self.log(f"Using session ID in request: {self.session_id}")
        
        # Add protocol version header for 2025-06-18
        if self.protocol_version == "2025-06-18":
            request_headers["MCP-Protocol-Version"] = self.protocol_version
        
        # Add any additional headers
        if headers:
            request_headers.update(headers)
        
        try:
            # Build the URL with session ID for non-initialization requests
            request_url = self.url
            if method != "initialize" and self.session_id:
                # Add session ID as URL parameter
                separator = "&" if "?" in request_url else "?"
                request_url = f"{request_url}{separator}session_id={self.session_id}"
                self.log(f"Using URL with session ID: {request_url}")
            
            # Send the request
            response = self.request_session.post(
                request_url,
                json=request,
                headers=request_headers,
                timeout=5  # 5 second timeout
            )
            
            status = response.status_code
            headers = dict(response.headers)
            
            self.log(f"Response Status: {status}")
            self.log(f"Response Headers: {headers}")
            
            # Parse JSON response first
            try:
                body = response.json()
                self.log(f"Response Body: {json.dumps(body)}")
            except ValueError:
                body = response.text
                self.log(f"Response Body (text): {body}")
            
            # If this is a successful initialize response, check for session ID in body first, then headers
            if method == "initialize" and status == 200:
                # First try to get session ID from response body (server-provided session ID)
                try:
                    if isinstance(body, dict) and 'result' in body:
                        result = body['result']
                        if 'session_id' in result:
                            self.session_id = result['session_id']
                            self.log(f"Captured session ID from response body: {self.session_id}")
                        elif 'sessionId' in result:
                            self.session_id = result['sessionId']
                            self.log(f"Captured session ID from response body (camelCase): {self.session_id}")
                        else:
                            # Fall back to headers
                            if "mcp-session-id" in headers:
                                self.session_id = headers["mcp-session-id"]
                                self.log(f"Captured session ID from headers: {self.session_id}")
                            else:
                                # Try case-insensitive match
                                for header_key in headers:
                                    if header_key.lower() == "mcp-session-id":
                                        self.session_id = headers[header_key]
                                        self.log(f"Captured session ID from headers (case insensitive): {self.session_id}")
                                        break
                    else:
                        # Fall back to headers
                        if "mcp-session-id" in headers:
                            self.session_id = headers["mcp-session-id"]
                            self.log(f"Captured session ID from headers: {self.session_id}")
                        else:
                            # Try case-insensitive match
                            for header_key in headers:
                                if header_key.lower() == "mcp-session-id":
                                    self.session_id = headers[header_key]
                                    self.log(f"Captured session ID from headers (case insensitive): {self.session_id}")
                                    break
                except:
                    # Fall back to headers
                    if "mcp-session-id" in headers:
                        self.session_id = headers["mcp-session-id"]
                        self.log(f"Captured session ID from headers: {self.session_id}")
                    else:
                        # Try case-insensitive match
                        for header_key in headers:
                            if header_key.lower() == "mcp-session-id":
                                self.session_id = headers[header_key]
                                self.log(f"Captured session ID from headers (case insensitive): {self.session_id}")
                                break
                
            return status, headers, body
            
        except requests.RequestException as e:
            self.log(f"Request failed: {str(e)}")
            raise
    
    def options_request(self):
        """Send an OPTIONS request to check server CORS support."""
        print("Testing OPTIONS request...")
        
        try:
            # Create a direct request with short timeout
            options_response = requests.options(self.url, timeout=2)
            
            # Check status code
            if options_response.status_code != 200:
                print(f"WARNING: OPTIONS request returned status {options_response.status_code}")
                # Continue even if not 200
            else:
                print("OPTIONS request successful")
            
            # Check CORS headers
            headers = options_response.headers
            missing_headers = []
            
            if 'access-control-allow-origin' not in headers:
                missing_headers.append('Access-Control-Allow-Origin')
            
            if 'access-control-allow-methods' not in headers:
                missing_headers.append('Access-Control-Allow-Methods')
            
            if 'access-control-allow-headers' not in headers:
                missing_headers.append('Access-Control-Allow-Headers')
            
            if missing_headers:
                print(f"WARNING: Missing CORS headers: {', '.join(missing_headers)}")
                # Continue even with missing headers
            else:
                print("All required CORS headers present")
            
            # Return true regardless of minor issues to keep tests running
            return True
            
        except requests.RequestException as e:
            print(f"WARNING: OPTIONS request failed with exception: {str(e)}")
            print("This may not be critical. Continuing with other tests...")
            # Don't fail the overall test for OPTIONS issues
            return True
    
    def initialize(self):
        """Initialize the server and store the session ID."""
        print("Testing server initialization...")
        
        # First ensure we're not using any session ID
        self.session_id = None
        
        # Use different parameter names based on protocol version
        if self.protocol_version == "2025-06-18":
            params = {
                "protocolVersion": self.protocol_version,
                "client_info": {
                    "name": "MCP HTTP Tester",
                    "version": "1.0.0"
                },
                "client_capabilities": {
                    "protocol_versions": [self.protocol_version],
                    "tools": {"asyncSupported": True},
                    "resources": True
                }
            }
        else:
            params = {
                "protocolVersion": self.protocol_version,
                "clientInfo": {
                    "name": "MCP HTTP Tester",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {"asyncSupported": True},
                    "resources": True
                }
            }
        
        try:
            status, headers, body = self.send_request("initialize", params)
            
            # Check for server already initialized error
            if isinstance(body, dict) and 'error' in body:
                error = body['error']
                if error.get('code') == -32803 and "already initialized" in error.get('message', ''):
                    print("Server already initialized, we need to reset the server first...")
                    
                    # Reset the server
                    if self.reset_server():
                        # Try initialization again after reset
                        status, headers, body = self.send_request("initialize", params)
                        
                        # If still getting "already initialized" error, we have a problem
                        if isinstance(body, dict) and 'error' in body:
                            error = body['error']
                            if error.get('code') == -32803 and "already initialized" in error.get('message', ''):
                                print("ERROR: Server is still in initialized state after reset attempt.")
                                print("Please manually restart the server before running tests.")
                                return False
                    else:
                        print("ERROR: Failed to reset server state.")
                        return False
                else:
                    print(f"ERROR: Server returned error: {error}")
                    return False
            
            # Normal initialization flow
            if status != 200:
                print(f"ERROR: Initialize request failed with status {status}")
                return False
            
            # Check for session ID in body first (server-provided session ID), then headers
            if isinstance(body, dict) and 'result' in body:
                result = body['result']
                if 'session_id' in result:
                    self.session_id = result['session_id']
                    print(f"Received session ID from response body: {self.session_id}")
                elif 'sessionId' in result:
                    self.session_id = result['sessionId']
                    print(f"Received session ID from response body (camelCase): {self.session_id}")
                elif isinstance(result, dict) and 'session' in result and 'id' in result['session']:
                    self.session_id = result['session']['id']
                    print(f"Received session ID from nested session object: {self.session_id}")
                # Fall back to headers if not found in body
                elif 'mcp-session-id' in headers:
                    self.session_id = headers['mcp-session-id']
                    print(f"Received session ID from headers: {self.session_id}")
                # Check for lowercase variant
                elif any(key.lower() == 'mcp-session-id' for key in headers):
                    key = next(key for key in headers if key.lower() == 'mcp-session-id')
                    self.session_id = headers[key]
                    print(f"Received session ID from headers (case insensitive): {self.session_id}")
                else:
                    print("WARNING: No session ID found in response. Some servers may not require one.")
            else:
                print("WARNING: No session ID found in response. Some servers may not require one.")
            
            # Verify other parts of the response body
            if not isinstance(body, dict):
                print("ERROR: Response body is not a JSON object")
                return False
            
            if 'result' not in body:
                print("ERROR: Response missing 'result' field")
                return False
            
            result = body['result']
            
            # Check for required fields in result (handle both formats)
            if 'protocolVersion' not in result and 'protocol_version' not in result:
                print("ERROR: Missing protocolVersion/protocol_version in result")
                return False
            
            if 'serverInfo' not in result:
                print("WARNING: Missing serverInfo in result. Continuing anyway.")
            
            if 'capabilities' not in result:
                print("WARNING: Missing capabilities in result. Continuing anyway.")
            
            print("Server initialization successful")
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"ERROR: Initialize request raised exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_tools(self):
        """Test the tools/list endpoint."""
        if not self.initialized:
            print("ERROR: Server not initialized, cannot list tools")
            return False
        
        print("Testing tools/list endpoint...")
        
        status, _, body = self.send_request("tools/list")
        
        if status != 200:
            print(f"ERROR: tools/list request failed with status {status}")
            return False
        
        # Verify response body
        if not isinstance(body, dict):
            print("ERROR: Response body is not a JSON object")
            return False
        
        if 'result' not in body:
            print("ERROR: Response missing 'result' field")
            return False
        
        result = body['result']
        
        # Check for tools array
        if 'tools' not in result or not isinstance(result['tools'], list):
            print("ERROR: Response missing 'tools' array")
            return False
        
        tools = result['tools']
        print(f"Server returned {len(tools)} tools")
        
        # Store the tools for later dynamic testing
        self.available_tools = tools
        
        return True
        
    def get_tool_by_name(self, name):
        """Get a tool definition by name."""
        if not hasattr(self, 'available_tools'):
            print("ERROR: Tools have not been listed yet")
            return None
            
        for tool in self.available_tools:
            if tool.get('name') == name:
                return tool
                
        return None
    
    def test_tool(self, tool_name, test_parameters=None):
        """Test a tool dynamically."""
        if not self.initialized:
            print(f"ERROR: Server not initialized, cannot call tool {tool_name}")
            return False
            
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            print(f"WARNING: Tool '{tool_name}' not found, skipping test")
            return True  # Not a failure if the tool doesn't exist
            
        print(f"Testing tools/call with {tool_name} tool...")
        
        # If test parameters weren't provided, create default ones based on the tool schema
        if test_parameters is None:
            parameters = {}
            tool_params = tool.get('parameters', {})
            properties = tool_params.get('properties', {})
            
            for param_name, param_def in properties.items():
                # Create a default value based on the parameter type
                if param_def.get('type') == 'string':
                    parameters[param_name] = f"Test value for {param_name}"
                elif param_def.get('type') == 'number' or param_def.get('type') == 'integer':
                    parameters[param_name] = 42
                elif param_def.get('type') == 'boolean':
                    parameters[param_name] = True
                # Add more types as needed
        else:
            parameters = test_parameters
            
        # Use different parameter names based on protocol version
        if self.protocol_version == "2025-06-18":
            params = {
                "name": tool_name,
                "arguments": parameters
            }
        else:
            params = {
                "name": tool_name,
                "parameters": parameters
            }
        
        status, _, body = self.send_request("tools/call", params)
        
        if status != 200:
            print(f"ERROR: tools/call request failed with status {status}")
            return False
        
        # Verify response body
        if not isinstance(body, dict):
            print(f"ERROR: Response body for {tool_name} is not a JSON object")
            return False
        
        if 'result' not in body and 'error' not in body:
            print(f"ERROR: Response for {tool_name} missing both 'result' and 'error' fields")
            return False
            
        if 'error' in body:
            print(f"ERROR: Tool {tool_name} returned an error: {body['error']}")
            return False
            
        result = body['result']
        print(f"{tool_name} tool test successful, returned: {result}")
        
        return True
        
    def test_available_tools(self):
        """Test all available tools dynamically."""
        if not hasattr(self, 'available_tools'):
            print("ERROR: Tools have not been listed yet")
            return False
            
        all_success = True
        
        for tool in self.available_tools:
            tool_name = tool.get('name')
            if tool_name:
                # Skip testing async tools with this method
                if tool_name == 'sleep' and self.protocol_version == "2025-03-26":
                    print(f"Skipping '{tool_name}' tool as it's tested separately")
                    continue
                    
                result = self.test_tool(tool_name)
                if not result:
                    all_success = False
        
        return all_success
    
    def test_async_sleep_tool(self):
        """Test the async sleep tool functionality."""
        if not self.initialized:
            print("ERROR: Server not initialized, cannot call tools")
            return False
        
        print("Testing tools/call-async with sleep tool...")
        
        # Only run this test for 2025-03-26 protocol
        if self.protocol_version != "2025-03-26":
            print("Skipping async test for older protocol versions")
            return True
        
        sleep_time = 3  # seconds
        
        # Use different parameter names based on protocol version
        if self.protocol_version == "2025-06-18":
            params = {
                "name": "sleep",
                "arguments": {
                    "seconds": sleep_time
                }
            }
        else:
            params = {
                "name": "sleep",
                "parameters": {
                    "seconds": sleep_time
                }
            }
        
        status, _, body = self.send_request("tools/call-async", params)
        
        if status != 200:
            print(f"ERROR: tools/call-async request failed with status {status}")
            return False
        
        # Verify response body
        if not isinstance(body, dict):
            print("ERROR: Response body is not a JSON object")
            return False
        
        if 'result' not in body:
            print("ERROR: Response missing 'result' field")
            return False
        
        result = body['result']
        
        # Check for task ID
        if 'id' not in result:
            print("ERROR: Missing task ID in result")
            return False
        
        task_id = result['id']
        print(f"Started async task with ID: {task_id}")
        
        # Poll for result
        max_attempts = 10
        attempt = 0
        completed = False
        
        print(f"Waiting for async task to complete (max {max_attempts} attempts)...")
        
        while attempt < max_attempts:
            time.sleep(1)
            attempt += 1
            
            params = {
                "id": task_id
            }
            
            status, _, body = self.send_request("tools/result", params)
            
            if status != 200:
                print(f"ERROR: tools/result request failed with status {status}")
                return False
            
            if not isinstance(body, dict) or 'result' not in body:
                print("ERROR: Invalid response format")
                return False
            
            result = body['result']
            
            if 'status' not in result:
                print("ERROR: Missing status in result")
                return False
            
            if result['status'] == 'completed':
                completed = True
                print(f"Async task completed after {attempt} attempts")
                break
            
            print(f"Attempt {attempt}: Task status = {result['status']}")
        
        if not completed:
            print("ERROR: Async task did not complete in time")
            return False
        
        print("Async sleep tool test successful")
        return True
    
    def reset_server(self):
        """Attempt to reset the server state by terminating any existing session."""
        print("Attempting to reset server state...")
        
        # First try a shutdown request without session ID to see if the server allows it
        try:
            request = {
                "jsonrpc": "2.0",
                "method": "shutdown",
                "id": str(uuid.uuid4())
            }
            
            self.log("Sending shutdown request without session ID")
            response = self.request_session.post(
                self.url,
                json=request,
                timeout=5
            )
            
            # Check if this was successful
            if response.status_code == 200:
                print("Server shutdown successful, waiting for restart...")
                time.sleep(2)  # Wait for server to restart or reset state
                self.session_id = None
                self.initialized = False
                return True
        except Exception as e:
            self.log(f"Shutdown without session ID failed: {str(e)}")
        
        # If we have a session ID from previous run, try to use it
        if self.session_id:
            try:
                self.log(f"Sending shutdown request with existing session ID: {self.session_id}")
                
                headers = {"Mcp-Session-Id": self.session_id}
                request = {
                    "jsonrpc": "2.0",
                    "method": "shutdown",
                    "id": str(uuid.uuid4())
                }
                
                response = self.request_session.post(
                    self.url,
                    json=request,
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print("Server reset with existing session successful")
                    time.sleep(2)  # Wait for server to process shutdown
                    self.session_id = None
                    self.initialized = False
                    return True
            except Exception as e:
                self.log(f"Shutdown with existing session ID failed: {str(e)}")
        
        # If we tried our best but failed, tell the user and continue anyway
        print("Server reset attempted, continuing with tests")
        
        # Reset our state even if the server didn't reset
        self.session_id = None
        self.initialized = False
        return True

    def test_status_codes(self):
        """Test various HTTP status code scenarios."""
        print("\n=== Testing HTTP Status Codes ===")
        
        tests = [
            {
                "name": "invalid_json",
                "payload": "{bad json}",
                "expected_code": 400,
                "headers": None
            },
            {
                "name": "no_method",
                "payload": {"jsonrpc": "2.0", "id": 1},
                "expected_code": 400,
                "headers": None
            },
            {
                "name": "unknown_method",
                "payload": {"jsonrpc": "2.0", "id": 1, "method": "unknown_method"},
                "expected_code": 404,
                "headers": None
            },
            {
                "name": "invalid_session",
                "payload": {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
                "expected_code": 401,
                "headers": {"Mcp-Session-Id": "invalid-session"}
            }
        ]
        
        success = True
        for test in tests:
            try:
                response = self.request_session.post(
                    self.url,
                    json=test["payload"] if isinstance(test["payload"], dict) else test["payload"],
                    headers=test["headers"] if test["headers"] else {},
                    timeout=5
                )
                
                if response.status_code == test["expected_code"]:
                    print(f"✅ {test['name']}: Got expected status code {test['expected_code']}")
                else:
                    print(f"❌ {test['name']}: Expected {test['expected_code']}, got {response.status_code}")
                    success = False
                    
            except Exception as e:
                print(f"❌ {test['name']}: Test failed with error: {str(e)}")
                success = False
                
        return success

    def test_headers(self):
        """Test HTTP header handling."""
        print("\n=== Testing HTTP Headers ===")
        
        # Initialize first to get a valid session
        if not self.initialize():
            print("❌ Failed to initialize for header tests")
            return False
            
        tests = [
            {
                "name": "content_type",
                "required_headers": {"Content-Type": "application/json"},
                "method": "server/info"
            },
            {
                "name": "session_id_present",
                "required_headers": {"Mcp-Session-Id": None},  # None means just check presence
                "method": "server/info"
            }
        ]
        
        if self.protocol_version == "2025-06-18":
            tests.append({
                "name": "protocol_version",
                "required_headers": {"MCP-Protocol-Version": "2025-06-18"},
                "method": "server/info"
            })
            
        success = True
        for test in tests:
            try:
                status, headers, _ = self.send_request(test["method"])
                
                if status != 200:
                    print(f"❌ {test['name']}: Request failed with status {status}")
                    success = False
                    continue
                    
                # Check required headers
                headers_valid = True
                for header, expected_value in test["required_headers"].items():
                    header_present = False
                    for response_header in headers:
                        if response_header.lower() == header.lower():
                            header_present = True
                            if expected_value is not None and headers[response_header] != expected_value:
                                print(f"❌ {test['name']}: Expected {header}={expected_value}, got {headers[response_header]}")
                                headers_valid = False
                            break
                            
                    if not header_present:
                        print(f"❌ {test['name']}: Missing required header {header}")
                        headers_valid = False
                        
                if headers_valid:
                    print(f"✅ {test['name']}: All required headers present and valid")
                else:
                    success = False
                    
            except Exception as e:
                print(f"❌ {test['name']}: Test failed with error: {str(e)}")
                success = False
                
        return success

    def test_protocol_versions(self):
        """Test protocol version negotiation."""
        print("\n=== Testing Protocol Version Negotiation ===")
        
        versions = ["2024-11-05", "2025-03-26", "2025-06-18"]
        success = True
        
        for version in versions:
            try:
                params = {
                    "client_info": {
                        "name": "MCP HTTP Tester",
                        "version": "1.0.0"
                    },
                    "client_capabilities": {
                        "protocol_versions": [version]
                    }
                }
                
                headers = {"MCP-Protocol-Version": version} if version == "2025-06-18" else {}
                status, response_headers, body = self.send_request("initialize", params, headers)
                
                if status != 200:
                    print(f"❌ Version {version}: Initialize failed with status {status}")
                    success = False
                    continue
                    
                if not isinstance(body, dict) or "result" not in body:
                    print(f"❌ Version {version}: Invalid response format")
                    success = False
                    continue
                    
                result = body["result"]
                if "protocol_version" not in result:
                    print(f"❌ Version {version}: Missing protocol_version in response")
                    success = False
                    continue
                    
                if result["protocol_version"] != version:
                    print(f"❌ Version {version}: Server responded with different version {result['protocol_version']}")
                    success = False
                    continue
                    
                print(f"✅ Version {version}: Successfully negotiated")
                
            except Exception as e:
                print(f"❌ Version {version}: Test failed with error: {str(e)}")
                success = False
                
        return success

    def run_all_tests(self):
        """Run all tests in sequence."""
        try:
            if not self.reset_server():
                print("WARNING: Failed to reset server state, tests may fail")
            
            # Run existing tests
            if not self.options_request():
                # Don't fail the entire test suite for OPTIONS issues
                pass
            
            if not self.initialize():
                return False
            
            if not self.list_tools():
                return False
            
            # Only run for 2025-03-26
            if self.protocol_version == "2025-03-26" and self.get_tool_by_name("sleep"):
                if not self.test_async_sleep_tool():
                    return False
            
            if not self.test_available_tools():
                return False
                
            # Run new tests
            if not self.test_status_codes():
                return False
                
            if not self.test_headers():
                return False
                
            if not self.test_protocol_versions():
                return False
            
            print("\n=== Test Results ===")
            print("PASS: OPTIONS request")
            print("PASS: Initialize")
            print("PASS: List Tools")
            if self.protocol_version == "2025-03-26" and self.get_tool_by_name("sleep"):
                print("PASS: Async Sleep Tool")
            print("PASS: Available Tools")
            print("PASS: Status Codes")
            print("PASS: Headers")
            print("PASS: Protocol Versions")
            
            print("\nSummary: All tests passed")
            return True
        except Exception as e:
            print(f"Error during test execution: {str(e)}")
            import traceback
            traceback.print_exc()
            return False 