#!/usr/bin/env python3
# Copyright (c) 2025 Scott Wilcox
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Minimal MCP-compliant server implementation.

This server is designed to be a minimal reference implementation that passes all validator tests.
It supports both 2024-11-05 and 2025-03-26 protocol versions.
"""

import os
import sys
import json
import logging
import uuid
import time
from typing import Dict, Any, Optional, List, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("minimal-mcp-stdio-server")

# Get environment variables
DEFAULT_PROTOCOL_VERSION = os.environ.get("MCP_PROTOCOL_VERSION", "2025-03-26")
DEBUG = os.environ.get("MCP_DEBUG", "").lower() in ("1", "true", "yes")

# Enable debug logging if requested
if DEBUG:
    logger.setLevel(logging.DEBUG)


class MinimalMCPServer:
    """Minimal MCP-compliant server implementation."""
    
    def __init__(self):
        """Initialize the server."""
        self.running = True
        self.negotiated_version = DEFAULT_PROTOCOL_VERSION
        self.client_capabilities = {}
        self.resources = {}
        self.pending_async_calls = {}  # Store pending async tool calls
        
        logger.info(f"Minimal MCP STDIO Server initializing")
        logger.info(f"Default protocol version: {DEFAULT_PROTOCOL_VERSION}")
    
    def run(self):
        """Run the server, processing stdin requests."""
        logger.info("Server started. Waiting for input...")
        
        # Main loop
        while self.running:
            try:
                # Read a line from stdin
                line = sys.stdin.readline()
                
                # Check for EOF
                if not line:
                    logger.info("End of input stream, shutting down")
                    break
                
                # Process the request
                self.process_request(line.strip())
                
            except KeyboardInterrupt:
                logger.info("Interrupted, shutting down")
                break
            except Exception as e:
                logger.error(f"Unhandled exception: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                sys.exit(1)
    
    def process_request(self, request_str: str):
        """
        Process a JSON-RPC request.
        
        Args:
            request_str: The JSON-RPC request string
        """
        if not request_str:
            return
            
        try:
            # Parse the request
            if DEBUG:
                logger.debug(f"Received: {request_str}")
                
            request = json.loads(request_str)
            
            # Check if it's a batch request
            if isinstance(request, list):
                self.process_batch_request(request)
                return
            
            # Extract the request components
            request_id = request.get("id")
            method = request.get("method", "")
            params = request.get("params", {})
            
            # Log the method call
            logger.info(f"Method call: {method}")
            
            # Process the request
            if request_id is not None:
                # This is a request (not a notification)
                try:
                    result = self.handle_method(method, params)
                    if result is not None:  # Only send response for non-None results
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result
                        }
                        self.send_response(response)
                except Exception as e:
                    logger.error(f"Error handling method {method}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # Create error response
                    error_code = -32000
                    if isinstance(e, MethodNotFoundError):
                        error_code = -32601
                    elif isinstance(e, InvalidParamsError):
                        error_code = -32602
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": error_code,
                            "message": str(e)
                        }
                    }
                    self.send_response(response)
            else:
                # This is a notification
                try:
                    self.handle_method(method, params)
                except Exception as e:
                    logger.error(f"Error handling notification {method}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {request_str}")
            # Send parse error for requests
            response = {
                "jsonrpc": "2.0",
                "id": None,  # We don't know the ID for invalid JSON
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            self.send_response(response)
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def process_batch_request(self, requests: List[Dict[str, Any]]):
        """
        Process a batch of JSON-RPC requests.
        
        Args:
            requests: List of request objects
        """
        responses = []
        
        for request in requests:
            request_id = request.get("id")
            method = request.get("method", "")
            params = request.get("params", {})
            
            # Only process requests with IDs (not notifications)
            if request_id is not None:
                try:
                    result = self.handle_method(method, params)
                    if result is not None:  # Only include response for non-None results
                        responses.append({
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result
                        })
                except Exception as e:
                    # Create error response
                    error_code = -32000
                    if isinstance(e, MethodNotFoundError):
                        error_code = -32601
                    elif isinstance(e, InvalidParamsError):
                        error_code = -32602
                    
                    responses.append({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": error_code,
                            "message": str(e)
                        }
                    })
            else:
                # Handle notification (no response needed)
                try:
                    self.handle_method(method, params)
                except Exception as e:
                    logger.error(f"Error handling notification {method}: {str(e)}")
        
        # Send batch response if there are any responses
        if responses:
            self.send_response(responses)
    
    def send_response(self, response: Union[Dict[str, Any], List[Dict[str, Any]]]):
        """
        Send a JSON-RPC response.
        
        Args:
            response: The JSON-RPC response object or batch of responses
        """
        response_str = json.dumps(response)
        if DEBUG:
            logger.debug(f"Sending: {response_str}")
        
        # Write the response to stdout
        print(response_str, flush=True)
    
    def handle_method(self, method: str, params: Dict[str, Any]) -> Any:
        """
        Handle an MCP method call.
        
        Args:
            method: The method name
            params: The method parameters
            
        Returns:
            The method result
            
        Raises:
            MethodNotFoundError: If the method is not supported
            InvalidParamsError: If the parameters are invalid
        """
        # Core protocol methods
        if method == "initialize":
            return self.handle_initialize(params)
        elif method == "initialized":
            return None  # Notification, no response needed
        elif method == "shutdown":
            self.running = False
            return {}
        elif method == "exit":
            self.running = False
            return None  # Notification, no response needed
            
        # Tools methods
        elif method == "tools/list":
            return self.handle_tools_list(params)
        elif method == "tools/call":
            return self.handle_tools_call(params)
        elif method == "tools/call-async":
            return self.handle_tools_call_async(params)
        elif method == "tools/result":
            return self.handle_tools_result(params)
        elif method == "tools/cancel":
            return self.handle_tools_cancel(params)
            
        # Server info method
        elif method == "server/info":
            return self.handle_server_info()
            
        # Resources methods (for 2025-03-26)
        elif method == "resources/list":
            return self.handle_resources_list()
        elif method == "resources/get":
            return self.handle_resources_get(params)
        elif method == "resources/create":
            return self.handle_resources_create(params)
            
        # Prompt methods (for testing prompt capabilities)
        elif method == "prompt/completion":
            return self.handle_prompt_completion(params)
        elif method == "prompt/models":
            return self.handle_prompt_models()
            
        # Unsupported method
        else:
            raise MethodNotFoundError(f"Method not found: {method}")
    
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the initialize method.
        
        Args:
            params: The initialization parameters
            
        Returns:
            The initialization result
            
        Raises:
            InvalidParamsError: If the parameters are invalid
        """
        if "protocolVersion" not in params:
            raise InvalidParamsError("Missing required parameter: protocolVersion")
            
        client_version = params.get("protocolVersion")
        if client_version not in ["2024-11-05", "2025-03-26"]:
            raise InvalidParamsError("Unsupported protocol version")
            
        # Store negotiated version
        self.negotiated_version = client_version
        
        # Store client info and capabilities
        self.client_info = params.get("clientInfo", {})
        self.client_capabilities = params.get("capabilities", {})
        
        # Check if this is a test client
        client_name = self.client_info.get("name", "").lower()
        if "test" in client_name:
            logger.info(f"Test client detected: {client_name}")
        
        # Build response
        response = {
            "protocolVersion": self.negotiated_version,
            "serverInfo": {
                "name": "Minimal MCP STDIO Server",
                "version": "1.0.0",
                "supportedVersions": ["2024-11-05", "2025-03-26"]
            }
        }
        
        # Add capabilities based on protocol version
        if self.negotiated_version == "2024-11-05":
            response["capabilities"] = {
                "tools": True
            }
        else:
            response["capabilities"] = {
                "tools": {
                    "asyncSupported": True
                },
                "resources": True
            }
        
        return response
    
    def handle_server_info(self) -> Dict[str, Any]:
        """
        Handle the server/info method.
        
        Returns:
            Server information
        """
        return {
            "name": "Minimal MCP STDIO Server",
            "version": "1.0.0",
            "supportedVersions": ["2024-11-05", "2025-03-26"]
        }
    
    def handle_tools_list(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle the tools/list method.
        
        Args:
            params: Optional method parameters
            
        Returns:
            A list of available tools
        """
        tools = []
        
        # Define tools based on protocol version
        if self.negotiated_version == "2024-11-05":
            tools = [
                {
                    "name": "echo",
                    "description": "Echo the input text",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to echo"
                            }
                        },
                        "required": ["text"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "echo": {
                                "type": "string"
                            }
                        }
                    }
                },
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {
                                "type": "number",
                                "description": "First number"
                            },
                            "b": {
                                "type": "number",
                                "description": "Second number"
                            }
                        },
                        "required": ["a", "b"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "sum": {
                                "type": "number"
                            }
                        }
                    }
                }
            ]
        else:
            tools = [
                {
                    "name": "echo",
                    "description": "Echo the input text",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Text to echo"
                            }
                        },
                        "required": ["message"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "echo": {
                                "type": "string"
                            }
                        }
                    }
                },
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {
                                "type": "number",
                                "description": "First number"
                            },
                            "b": {
                                "type": "number",
                                "description": "Second number"
                            }
                        },
                        "required": ["a", "b"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "sum": {
                                "type": "number"
                            }
                        }
                    }
                },
                {
                    "name": "sleep",
                    "description": "Sleep for a specified duration (useful for testing async functionality)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "seconds": {
                                "type": "number",
                                "description": "Sleep duration in seconds"
                            }
                        },
                        "required": ["seconds"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "slept": {
                                "type": "number"
                            }
                        }
                    }
                }
            ]
        
        result = {"tools": tools}
        print(f"DEBUG: handle_tools_list returning: {json.dumps(result)}")
        return result
    
    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
<<<<<<< Updated upstream:ref_stdio_server/stdio_server_2025_03_26.py
        """Handle the tools/call method."""
=======
        """
        Handle the tools/call method.
        
        Args:
            params: The method parameters
            
        Returns:
            The tool result
            
        Raises:
            InvalidParamsError: If the parameters are invalid
        """
        # Debug logging
        print(f"DEBUG: handle_tools_call received params: {json.dumps(params)}")
        
>>>>>>> Stashed changes:minimal_mcp_server/minimal_mcp_server.py
        if "name" not in params:
            raise InvalidParamsError("Missing required parameter: name")
        if "arguments" not in params:
            raise InvalidParamsError("Missing required parameter: arguments")
            
<<<<<<< Updated upstream:ref_stdio_server/stdio_server_2025_03_26.py
        tool_name = params["name"]
        arguments = params["arguments"]
=======
        tool_name = params.get("name", "")
        
        # Support multiple parameter naming conventions for compatibility with different clients
        arguments = params.get("arguments", {})
        if not arguments:
            # Try alternate parameter names
            if "parameters" in params:
                arguments = params.get("parameters", {})
                print(f"DEBUG: Using 'parameters' instead of 'arguments': {json.dumps(arguments)}")
            elif "params" in params:
                arguments = params.get("params", {})
                print(f"DEBUG: Using 'params' instead of 'arguments': {json.dumps(arguments)}")
        
        # Debug logging 
        print(f"DEBUG: tool_name={tool_name}, arguments={json.dumps(arguments)}")
>>>>>>> Stashed changes:minimal_mcp_server/minimal_mcp_server.py
        
        # Find the tool
        tool = None
        for t in self.handle_tools_list()["tools"]:
            if t["name"] == tool_name:
                tool = t
                break
                
        if not tool:
            raise InvalidParamsError(f"Unknown tool: {tool_name}")
            
        # Handle each tool
        if tool_name == "echo":
<<<<<<< Updated upstream:ref_stdio_server/stdio_server_2025_03_26.py
            # Check for either message or text parameter
            message = arguments.get("message") or arguments.get("text")
            if not message:
                raise InvalidParamsError("Missing required argument: message")
            return {"content": {"echo": message}}
            
=======
            if "text" not in arguments and "message" not in arguments:
                raise InvalidParamsError("Missing required argument: text")
            
            # Support both 'text' and 'message' parameter names
            message = arguments.get("text", arguments.get("message", ""))
            
            # Return immediately with simplified result
            print(f"ECHO TOOL CALLED WITH: {message}")
            return {
                "content": {
                    "echo": message
                }
            }
>>>>>>> Stashed changes:minimal_mcp_server/minimal_mcp_server.py
        elif tool_name == "add":
            # Validate required parameters
            if "a" not in arguments or "b" not in arguments:
                raise InvalidParamsError("Missing required arguments: a, b")
            try:
                a = float(arguments["a"])
                b = float(arguments["b"])
                return {"content": {"sum": a + b}}
            except (TypeError, ValueError):
                raise InvalidParamsError("Arguments 'a' and 'b' must be numbers")
                
        elif tool_name == "sleep":
<<<<<<< Updated upstream:ref_stdio_server/stdio_server_2025_03_26.py
            # Validate required parameters
            seconds = arguments.get("seconds") or arguments.get("duration")
            if not seconds:
                raise InvalidParamsError("Missing required argument: seconds")
            try:
                seconds = float(seconds)
                time.sleep(seconds)
                return {"content": {"slept": seconds}}
            except (TypeError, ValueError):
                raise InvalidParamsError("Argument 'seconds' must be a number")
                
=======
            if "duration" not in arguments and "seconds" not in arguments:
                raise InvalidParamsError("Missing required argument: duration or seconds")
            try:
                # Support both 'duration' and 'seconds' parameter names
                duration = float(arguments.get("duration", arguments.get("seconds", 0)))
                
                if duration > 10:  # Limit sleep duration for safety
                    duration = 10
                # For synchronous call, actually sleep
                time.sleep(duration)
                return {
                    "content": {
                        "slept": duration
                    }
                }
            except ValueError:
                raise InvalidParamsError("Duration must be a number")
        elif tool_name == "list_directory":
            if "path" not in arguments:
                raise InvalidParamsError("Missing required argument: path")
            # Simulate directory listing
            path = arguments["path"]
            # In a real server, this would list actual directory contents
            items = [
                {"name": "file1.txt", "type": "file"},
                {"name": "file2.txt", "type": "file"},
                {"name": "subdir", "type": "directory"}
            ]
            return {
                "content": {
                    "items": items
                }
            }
        elif tool_name == "read_file":
            if "path" not in arguments:
                raise InvalidParamsError("Missing required argument: path")
            # Simulate file reading
            path = arguments["path"]
            # In a real server, this would read actual file contents
            content = f"This is the content of {path}"
            return {
                "content": {
                    "content": content
                }
            }
        elif tool_name == "write_file":
            if "path" not in arguments or "content" not in arguments:
                raise InvalidParamsError("Missing required arguments: path, content")
            # Simulate file writing
            path = arguments["path"]
            content = arguments["content"]
            # In a real server, this would write to actual file
            return {
                "content": {
                    "success": True
                }
            }
>>>>>>> Stashed changes:minimal_mcp_server/minimal_mcp_server.py
        else:
            raise InvalidParamsError(f"Unknown tool: {tool_name}")
    
    def handle_tools_call_async(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the tools/call-async method.
        
        Args:
            params: The method parameters
            
        Returns:
            The async tool call ID
            
        Raises:
            InvalidParamsError: If the parameters are invalid
        """
        # Debug logging
        print(f"DEBUG: handle_tools_call_async received params: {json.dumps(params)}")
        
        if self.negotiated_version != "2025-03-26":
            raise MethodNotFoundError("Async tool calls are only supported in protocol version 2025-03-26")
            
        if "name" not in params:
            raise InvalidParamsError("Missing required parameter: name")
            
        tool_name = params.get("name", "")
        
        # Support multiple parameter naming conventions for compatibility with different clients
        arguments = params.get("arguments", {})
        if not arguments:
            # Try alternate parameter names
            if "parameters" in params:
                arguments = params.get("parameters", {})
                print(f"DEBUG: Using 'parameters' instead of 'arguments': {json.dumps(arguments)}")
            elif "params" in params:
                arguments = params.get("params", {})
                print(f"DEBUG: Using 'params' instead of 'arguments': {json.dumps(arguments)}")
        
        # Generate a call ID
        call_id = str(uuid.uuid4())
        
        # Store the call details for later processing
        self.pending_async_calls[call_id] = {
            "name": tool_name,
            "arguments": arguments,
            "status": "running",
            "createdAt": int(time.time() * 1000),
            "result": None,
            "error": None
        }
        
        # For sleep tool, store the requested duration
        if tool_name == "sleep" and "duration" in arguments:
            try:
                duration = float(arguments["duration"])
                if duration > 10:  # Limit sleep duration for safety
                    duration = 10
                self.pending_async_calls[call_id]["sleepDuration"] = duration
            except (ValueError, TypeError):
                # Handle invalid duration in get_result
                pass
        
        # Return the call ID immediately
        return {
            "id": call_id
        }
    
    def handle_tools_result(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the tools/result method.
        
        Args:
            params: The method parameters
            
        Returns:
            The tool result or status
            
        Raises:
            InvalidParamsError: If the parameters are invalid
        """
        if self.negotiated_version != "2025-03-26":
            raise MethodNotFoundError("Async tool calls are only supported in protocol version 2025-03-26")
            
        if "id" not in params:
            raise InvalidParamsError("Missing required parameter: id")
            
        call_id = params.get("id", "")
        
        # Check if the call exists
        if call_id not in self.pending_async_calls:
            raise InvalidParamsError(f"Tool call not found: {call_id}")
            
        call_info = self.pending_async_calls[call_id]
        
        # If the call is still running, check if it should be completed
        if call_info["status"] == "running":
            tool_name = call_info["name"]
            arguments = call_info["arguments"]
            current_time = int(time.time() * 1000)
            elapsed_seconds = (current_time - call_info["createdAt"]) / 1000
            
            # Special handling for sleep tool
            if tool_name == "sleep" and "sleepDuration" in call_info:
                sleep_duration = call_info["sleepDuration"]
                
                # Check if the sleep duration has elapsed
                if elapsed_seconds >= sleep_duration:
                    # Sleep completed
                    call_info["status"] = "completed"
                    call_info["result"] = {"slept": sleep_duration}
                    call_info["completedAt"] = current_time
                else:
                    # Sleep still in progress
                    return {
                        "status": "running"
                    }
            else:
                try:
                    # Execute other tools (immediately)
                    result = None
                    if tool_name == "echo":
                        if "text" not in arguments:
                            raise InvalidParamsError("Missing required argument: text")
                        result = {
                            "echo": arguments["text"]
                        }
                    elif tool_name == "add":
                        if "a" not in arguments or "b" not in arguments:
                            raise InvalidParamsError("Missing required arguments: a, b")
                        try:
                            a = float(arguments["a"])
                            b = float(arguments["b"])
                            result = {
                                "sum": a + b
                            }
                        except ValueError:
                            raise InvalidParamsError("Arguments must be numbers")
                    elif tool_name == "sleep":
                        if "duration" not in arguments:
                            raise InvalidParamsError("Missing required argument: duration")
                        try:
                            duration = float(arguments["duration"])
                            if duration > 10:  # Limit sleep duration for safety
                                duration = 10
                            result = {
                                "slept": duration
                            }
                        except ValueError:
                            raise InvalidParamsError("Duration must be a number")
                    elif tool_name in ["list_directory", "read_file", "write_file"]:
                        # Simulate the execution of these tools
                        result = {"success": True, "message": f"Async {tool_name} completed"}
                    else:
                        raise MethodNotFoundError(f"Tool not found: {tool_name}")
                    
                    # Update the call info
                    call_info["status"] = "completed"
                    call_info["result"] = result
                    call_info["completedAt"] = current_time
                    
                except Exception as e:
                    # Handle errors
                    call_info["status"] = "error"
                    call_info["error"] = str(e)
                    call_info["completedAt"] = current_time
        
        # Return the current status of the call
        response = {
            "status": call_info["status"]
        }
        
        if call_info["status"] == "completed":
            response["content"] = call_info["result"]
        elif call_info["status"] == "error":
            response["error"] = call_info["error"]
            
        return response
    
    def handle_tools_cancel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the tools/cancel method.
        
        Args:
            params: The method parameters
            
        Returns:
            The cancel result
            
        Raises:
            InvalidParamsError: If the parameters are invalid
        """
        if self.negotiated_version != "2025-03-26":
            raise MethodNotFoundError("Async tool calls are only supported in protocol version 2025-03-26")
            
        if "id" not in params:
            raise InvalidParamsError("Missing required parameter: id")
            
        call_id = params.get("id", "")
        
        # Check if the call exists
        if call_id not in self.pending_async_calls:
            raise InvalidParamsError(f"Tool call not found: {call_id}")
            
        # Cancel the call
        call_info = self.pending_async_calls[call_id]
        if call_info["status"] == "running":
            # Mark as cancelled (use British spelling with two l's)
            call_info["status"] = "cancelled"
            call_info["canceledAt"] = int(time.time() * 1000)
            
        return {
            "success": True
        }
    
    def handle_resources_list(self) -> Dict[str, Any]:
        """
        Handle the resources/list method.
        
        Returns:
            List of resources
        """
        resources_list = []
        for resource_id, resource in self.resources.items():
            resources_list.append({
                "id": resource_id,
                "uri": f"mcp://resources/{resource_id}",
                "name": resource.get("data", {}).get("name", f"Resource {resource_id}"),
                "type": resource["type"],
                "createdAt": resource["createdAt"]
            })
        
        # If there are no resources created yet, add a sample one
        if not resources_list:
            sample_id = "sample-resource-id"
            self.resources[sample_id] = {
                "type": "document",
                "data": {
                    "name": "Sample Document",
                    "content": "This is a sample document for testing."
                },
                "createdAt": int(time.time() * 1000)
            }
            resources_list.append({
                "id": sample_id,
                "uri": f"mcp://resources/{sample_id}",
                "name": "Sample Document",
                "type": "document",
                "createdAt": self.resources[sample_id]["createdAt"]
            })
        
        return {
            "resources": resources_list
        }
    
    def handle_resources_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the resources/get method.
        
        Args:
            params: The method parameters
            
        Returns:
            The resource details
            
        Raises:
            InvalidParamsError: If the parameters are invalid
        """
        if "id" not in params:
            raise InvalidParamsError("Missing required parameter: id")
            
        resource_id = params["id"]
        
        # Handle URI format (mcp://resources/id)
        if resource_id.startswith("mcp://resources/"):
            resource_id = resource_id.replace("mcp://resources/", "")
        
        # Check if the resource exists
        if resource_id in self.resources:
            resource = self.resources[resource_id]
            return {
                "id": resource_id,
                "uri": f"mcp://resources/{resource_id}",
                "name": resource.get("data", {}).get("name", f"Resource {resource_id}"),
                "type": resource["type"],
                "data": resource["data"],
                "createdAt": resource["createdAt"],
                "contents": [{
                    "uri": f"mcp://resources/{resource_id}/content",
                    "text": resource.get("data", {}).get("content", "")
                }]
            }
        # Handle the sample resource for backward compatibility
        elif resource_id == "sample-doc":
            sample_id = "sample-doc"
            self.resources[sample_id] = {
                "type": "document",
                "data": {
                    "name": "Sample Document",
                    "content": "This is a sample document for testing."
                },
                "createdAt": int(time.time() * 1000)
            }
            resource = self.resources[sample_id]
            return {
                "id": sample_id,
                "uri": f"mcp://resources/{sample_id}",
                "name": "Sample Document",
                "type": resource["type"],
                "data": resource["data"],
                "createdAt": resource["createdAt"],
                "contents": [{
                    "uri": f"mcp://resources/{sample_id}/content",
                    "text": "This is a sample document for testing."
                }]
            }
        else:
            raise InvalidParamsError(f"Resource not found: {resource_id}")
    
    def handle_resources_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the resources/create method.
        
        Args:
            params: The method parameters
            
        Returns:
            The created resource ID
            
        Raises:
            InvalidParamsError: If the parameters are invalid
        """
        if "type" not in params:
            raise InvalidParamsError("Missing required parameter: type")
            
        resource_type = params["type"]
        resource_data = params.get("data", {})
        
        # Generate a unique ID
        resource_id = str(uuid.uuid4())
        
        # Store the resource
        self.resources[resource_id] = {
            "type": resource_type,
            "data": resource_data,
            "createdAt": int(time.time() * 1000)  # Timestamp in milliseconds
        }
        
        return {
            "id": resource_id
        }
    
    def handle_prompt_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the prompt/completion method.
        
        Args:
            params: The method parameters
            
        Returns:
            The completion result
            
        Raises:
            InvalidParamsError: If required parameters are missing
        """
        if "prompt" not in params:
            raise InvalidParamsError("Missing required parameter: prompt")
            
        prompt = params.get("prompt")
        
        # Simulate a simple completion
        return {
            "completion": f"This is a response to: {prompt}",
            "model": "minimal-model-1.0"
        }
    
    def handle_prompt_models(self) -> Dict[str, Any]:
        """
        Handle the prompt/models method.
        
        Returns:
            List of available models
        """
        models = [
            {
                "id": "minimal-model-1.0",
                "name": "Minimal Model 1.0",
                "capabilities": {
                    "streaming": True
                }
            }
        ]
        
        return {"models": models}


class MethodNotFoundError(Exception):
    """Exception raised when a method is not found."""
    pass


class InvalidParamsError(Exception):
    """Exception raised when parameters are invalid."""
    pass


def main():
    """Main entry point."""
    try:
        server = MinimalMCPServer()
        server.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main() 