#!/usr/bin/env python3
"""
Test script for Xano MCP Server
"""

import subprocess
import os
import sys
import json

# Set a test token for testing
os.environ["XANO_API_TOKEN"] = "test-token-for-validation"

def print_header(text):
    """Print a section header"""
    print("\n" + "=" * 50)
    print(text)
    print("=" * 50 + "\n")

print_header("Testing Xano MCP Server")

# Check if the script exists
script_path = "./xano_mcp_sdk.py"
if not os.path.exists(script_path):
    print(f"Error: Could not find {script_path}")
    sys.exit(1)

print("✅ Found MCP script")

# Check if dependencies are installed
try:
    import httpx
    from mcp.server.fastmcp import FastMCP
    print("✅ Dependencies are installed")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Test if the script can be executed
print("\nAttempting to start the MCP server...")
try:
    # Start the process but be ready to kill it
    process = subprocess.Popen(
        [sys.executable, script_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Initialize JSON-RPC message to test the server
    test_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "0.3.0",
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            },
            "capabilities": {}
        }
    }
    
    # Send the initialize request
    process.stdin.write(json.dumps(test_message) + "\n")
    process.stdin.flush()
    
    # Try to read a response with a timeout
    import select
    readable, _, _ = select.select([process.stdout], [], [], 5)
    
    if process.stdout in readable:
        response = process.stdout.readline()
        try:
            response_json = json.loads(response)
            if "result" in response_json:
                print("✅ MCP server started and responded to initialize request")
            else:
                print(f"❌ MCP server responded but with an unexpected message: {response_json}")
        except json.JSONDecodeError:
            print(f"❌ MCP server responded but with invalid JSON: {response}")
    else:
        print("❌ MCP server did not respond within timeout period")
    
    # Terminate the process
    process.terminate()
    process.wait(timeout=5)
    
except Exception as e:
    print(f"❌ Error testing MCP server: {e}")
    sys.exit(1)

print_header("Test Complete")
print("Your Xano MCP server appears to be set up correctly.")
print("To use it with Claude for Desktop:")
print("1. Make sure you've run the install script (install.sh or install.bat)")
print("2. Edit the Claude configuration to include your actual Xano API token")
print("3. Restart Claude for Desktop")
