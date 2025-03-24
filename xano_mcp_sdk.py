#!/usr/bin/env python3
"""
Xano MCP Server - Simplified version
"""

import os
import sys
import json
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("xano")

# Constants
XANO_GLOBAL_API = "https://app.xano.com/api:meta"

def get_token():
    """Get the Xano API token from environment or arguments"""
    # Try environment variables with different names
    for env_var in ["XANO_API_TOKEN", "xanoApiToken"]:
        token = os.environ.get(env_var)
        if token:
            print(f"Found token in environment variable: {env_var}", file=sys.stderr)
            return token
    
    # Try command line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--token" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    
    # Debug info for environment variables
    print("Available environment variables:", file=sys.stderr)
    for key, value in os.environ.items():
        print(f"  {key}: {'*' * min(len(value), 5)}", file=sys.stderr)
    
    print("Error: Xano API token not provided.", file=sys.stderr)
    print("Please set XANO_API_TOKEN environment variable or use --token argument", file=sys.stderr)
    return "missing_token"  # Return a placeholder instead of exiting

async def make_api_request(url, headers, method="GET", params=None, data=None):
    """Helper function to make API requests"""
    try:
        print(f"Making {method} request to {url}", file=sys.stderr)
        print(f"Headers: {headers}", file=sys.stderr)
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            print(f"Response status: {response.status_code}", file=sys.stderr)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_message = f"API request failed with status {response.status_code}"
                try:
                    error_response = response.text
                    print(f"Error response: {error_response[:200]}", file=sys.stderr)
                except:
                    pass
                return {"error": error_message}
    except Exception as e:
        error_message = f"Exception during API request: {str(e)}"
        print(error_message, file=sys.stderr)
        return {"error": error_message}

@mcp.tool()
async def xano_list_instances():
    """List all Xano instances associated with the account."""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    result = await make_api_request(f"{XANO_GLOBAL_API}/auth/me", headers)
    if "error" not in result and "instances" in result:
        return {"instances": result["instances"]}
    return {"error": "Failed to list instances", "details": result.get("error", "Unknown error")}

@mcp.tool()
async def xano_get_instance_details(instance_name: str):
    """Get details for a specific Xano instance."""
    instance_domain = f"{instance_name}.n7c.xano.io"
    return {
        "name": instance_name,
        "display": instance_name.split("-")[0].upper(),
        "xano_domain": instance_domain,
        "meta_api": f"https://{instance_domain}/api:meta",
    }

@mcp.tool()
async def xano_list_databases(instance_name: str):
    """List all databases (workspaces) in a specific Xano instance."""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"
    url = f"{meta_api}/workspace"
    result = await make_api_request(url, headers)
    return {"databases": result} if "error" not in result else result

@mcp.tool()
async def xano_list_tables(instance_name: str, database_name: str):
    """List all tables in a specific Xano database (workspace)."""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"
    url = f"{meta_api}/workspace/{database_name}/table"
    result = await make_api_request(url, headers)
    if "error" in result:
        return result
    return {"tables": result if "items" not in result else result["items"]}

@mcp.tool()
async def xano_get_table_details(instance_name: str, workspace_id: str, table_id: str):
    """Get details for a specific Xano table."""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"
    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}"
    return await make_api_request(url, headers)

if __name__ == "__main__":
    print("Starting Xano MCP server...", file=sys.stderr)
    print(f"Command line args: {sys.argv}", file=sys.stderr)
    mcp.run(transport="stdio")
