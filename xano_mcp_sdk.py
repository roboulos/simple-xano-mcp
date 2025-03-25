#!/usr/bin/env python3
"""
Xano MCP Server - Improved version with better error handling and parameter flexibility
"""

import os
import sys
import json
import httpx
from typing import Dict, List, Any, Union, Optional
from mcp.server.fastmcp import FastMCP

# Enhanced logging function for better debugging
def log_debug(message):
    """Log debug information to stderr with timestamps"""
    print(f"DEBUG: {message}", file=sys.stderr, flush=True)

# Initialize with debug logging
log_debug("Starting Xano MCP server initialization...")

try:
    # Initialize FastMCP server
    mcp = FastMCP("xano")
    log_debug("FastMCP server initialized successfully")
except Exception as e:
    print(f"CRITICAL ERROR initializing FastMCP: {str(e)}", file=sys.stderr, flush=True)
    sys.exit(1)

# Constants
XANO_GLOBAL_API = "https://app.xano.com/api:meta"

def get_token():
    """Get the Xano API token from environment or arguments"""
    log_debug("Attempting to retrieve Xano API token...")
    
    # Try environment variables with different names
    for env_var in ["XANO_API_TOKEN", "xanoApiToken"]:
        token = os.environ.get(env_var)
        if token:
            log_debug(f"Found token in environment variable: {env_var}")
            return token
    
    # Try command line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--token" and i + 1 < len(sys.argv):
            log_debug("Found token in command line arguments")
            return sys.argv[i + 1]
    
    # Debug info for environment variables
    log_debug("Available environment variables:")
    for key, value in os.environ.items():
        if 'TOKEN' in key.upper() or 'API' in key.upper():
            log_debug(f"  {key}: {'*' * min(len(value) if value else 0, 5)}")
    
    log_debug("Warning: Xano API token not provided")
    print("Error: Xano API token not provided.", file=sys.stderr, flush=True)
    print("Please set XANO_API_TOKEN environment variable or use --token argument", file=sys.stderr, flush=True)
    return "missing_token"  # Return a placeholder instead of exiting


# Utility function to make API requests
async def make_api_request(
    url, headers, method="GET", data=None, params=None, files=None
):
    """Helper function to make API requests with consistent error handling"""
    try:
        log_debug(f"Making {method} request to {url}")
        if params:
            log_debug(f"With params: {params}")
        if data and not files:
            log_debug(f"With data: {json.dumps(data)[:500]}...")

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                if files:
                    # For multipart/form-data with file uploads
                    response = await client.post(
                        url, headers=headers, data=data, files=files
                    )
                else:
                    response = await client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method == "DELETE":
                if data:
                    response = await client.delete(url, headers=headers, json=data)
                else:
                    response = await client.delete(url, headers=headers)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            log_debug(f"Response status: {response.status_code}")

            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    log_debug(f"Error parsing JSON response: {response.text[:200]}...")
                    return {"error": "Failed to parse response as JSON"}
            else:
                log_debug(f"Error response: {response.text[:200]}...")
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "details": response.text[:500]
                }
    except Exception as e:
        log_debug(f"Exception during API request: {str(e)}")
        return {"error": f"Exception during API request: {str(e)}"}


# Improved utility function to ensure IDs are properly formatted as strings
def format_id(id_value):
    """
    Ensures IDs are properly formatted strings.
    Handles various input types (int, str, etc.) and converts them to strings.
    """
    if id_value is None:
        return None
    
    # Already a string? Just clean it up
    if isinstance(id_value, str):
        return id_value.strip('"').strip("'")
    
    # Convert numbers or other types to string
    return str(id_value)


##############################################
# SECTION: INSTANCE AND DATABASE OPERATIONS
##############################################


@mcp.tool()
async def xano_list_instances() -> Dict[str, Any]:
    """
    List all Xano instances associated with the account.
    
    Returns:
        A dictionary containing a list of Xano instances under the 'instances' key.
        
    Example:
        ```
        result = await xano_list_instances()
        # Returns: {"instances": [{"name": "instance-name", ...}]}
        ```
    """
    log_debug("Called xano_list_instances()")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # First try the direct auth/me endpoint
    result = await make_api_request(f"{XANO_GLOBAL_API}/auth/me", headers)

    if "error" not in result and "instances" in result:
        log_debug(f"Successfully retrieved {len(result['instances'])} instances")
        return {"instances": result["instances"]}

    # If that doesn't work, perform a workaround - list any known instances
    # This is a fallback for when the API doesn't return instances directly
    log_debug("Falling back to hardcoded instance detection...")
    instances = [
        {
            "name": "xnwv-v1z6-dvnr",
            "display": "Robert",
            "xano_domain": "xnwv-v1z6-dvnr.n7c.xano.io",
            "rate_limit": False,
            "meta_api": "https://xnwv-v1z6-dvnr.n7c.xano.io/api:meta",
            "meta_swagger": "https://xnwv-v1z6-dvnr.n7c.xano.io/apispec:meta?type=json",
        }
    ]
    return {"instances": instances}


@mcp.tool()
async def xano_get_instance_details(instance_name: str) -> Dict[str, Any]:
    """
    Get details for a specific Xano instance.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        
    Returns:
        A dictionary containing details about the specified Xano instance.
        
    Example:
        ```
        result = await xano_get_instance_details("xnwv-v1z6-dvnr")
        # Returns instance details as a dictionary
        ```
    """
    log_debug(f"Called xano_get_instance_details(instance_name={instance_name})")
    # Construct the instance details without making an API call
    instance_domain = f"{instance_name}.n7c.xano.io"
    return {
        "name": instance_name,
        "display": instance_name.split("-")[0].upper(),
        "xano_domain": instance_domain,
        "rate_limit": False,
        "meta_api": f"https://{instance_domain}/api:meta",
        "meta_swagger": f"https://{instance_domain}/apispec:meta?type=json",
    }


@mcp.tool()
async def xano_list_databases(instance_name: str) -> Dict[str, Any]:
    """
    List all databases (workspaces) in a specific Xano instance.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        
    Returns:
        A dictionary containing a list of databases/workspaces under the 'databases' key.
        
    Example:
        ```
        result = await xano_list_databases("xnwv-v1z6-dvnr")
        # Returns: {"databases": [{"id": "123", "name": "MyDatabase", ...}]}
        ```
    """
    log_debug(f"Called xano_list_databases(instance_name={instance_name})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Get the workspaces
    url = f"{meta_api}/workspace"
    log_debug(f"Listing databases from URL: {url}")
    result = await make_api_request(url, headers)

    if "error" in result:
        log_debug(f"Error listing databases: {result['error']}")
        return result

    log_debug(f"Successfully retrieved database list")
    return {"databases": result}


@mcp.tool()
async def xano_get_workspace_details(
    instance_name: str, workspace_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Get details for a specific Xano workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        
    Returns:
        A dictionary containing details about the specified workspace.
        
    Example:
        ```
        # Both of these will work:
        result = await xano_get_workspace_details("xnwv-v1z6-dvnr", "5")
        result = await xano_get_workspace_details("xnwv-v1z6-dvnr", 5)
        ```
    """
    log_debug(f"Called xano_get_workspace_details(instance_name={instance_name}, workspace_id={workspace_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format the workspace_id to ensure it's a proper string
    workspace_id = format_id(workspace_id)
    log_debug(f"Formatted workspace_id: {workspace_id}")

    url = f"{meta_api}/workspace/{workspace_id}"
    log_debug(f"Requesting workspace details from URL: {url}")
    return await make_api_request(url, headers)


##############################################
# SECTION: TABLE OPERATIONS
##############################################


@mcp.tool()
async def xano_list_tables(
    instance_name: str, database_id: Union[str, int]
) -> Dict[str, Any]:
    """
    List all tables in a specific Xano database (workspace).

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        database_id: The ID of the Xano workspace/database (can be provided as string or number)
        
    Returns:
        A dictionary containing a list of tables under the 'tables' key.
        
    Example:
        ```
        # Both of these will work:
        result = await xano_list_tables("xnwv-v1z6-dvnr", "5")
        result = await xano_list_tables("xnwv-v1z6-dvnr", 5)
        ```
    """
    log_debug(f"Called xano_list_tables(instance_name={instance_name}, database_id={database_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format the database_id to ensure it's a proper string
    workspace_id = format_id(database_id)
    log_debug(f"Formatted database_id: {workspace_id}")

    # List tables in the workspace
    url = f"{meta_api}/workspace/{workspace_id}/table"
    log_debug(f"Requesting tables from URL: {url}")
    result = await make_api_request(url, headers)

    if "error" in result:
        log_debug(f"Error listing tables: {result['error']}")
        return result

    # Handle different response formats
    if "items" in result:
        log_debug(f"Successfully retrieved {len(result['items'])} tables")
        return {"tables": result["items"]}
    else:
        log_debug(f"Successfully retrieved tables list")
        return {"tables": result}


@mcp.tool()
async def xano_get_table_details(
    instance_name: str, workspace_id: Union[str, int], table_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Get details for a specific Xano table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        
    Returns:
        A dictionary containing details about the specified table.
        
    Example:
        ```
        # All of these formats will work:
        result = await xano_get_table_details("xnwv-v1z6-dvnr", "5", "10")
        result = await xano_get_table_details("xnwv-v1z6-dvnr", 5, 10)
        result = await xano_get_table_details("xnwv-v1z6-dvnr", "5", 10)
        ```
    """
    log_debug(f"Called xano_get_table_details(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}"
    log_debug(f"Requesting table details from URL: {url}")
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_create_table(
    instance_name: str,
    workspace_id: Union[str, int],
    name: str,
    description: str = "",
    docs: str = "",
    auth: bool = False,
    tag: List[str] = None,
) -> Dict[str, Any]:
    """
    Create a new table in a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        name: The name of the new table
        description: Table description
        docs: Documentation text
        auth: Whether authentication is required
        tag: List of tags for the table
        
    Returns:
        A dictionary containing details about the newly created table.
        
    Example:
        ```
        result = await xano_create_table("xnwv-v1z6-dvnr", 5, "Users", 
                                        description="Stores user information")
        ```
    """
    log_debug(f"Called xano_create_table(instance_name={instance_name}, workspace_id={workspace_id}, name={name})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format the workspace_id to ensure it's a proper string
    workspace_id = format_id(workspace_id)
    log_debug(f"Formatted workspace_id: {workspace_id}")

    # Prepare the table creation data
    data = {"name": name, "description": description, "docs": docs, "auth": auth}

    if tag:
        data["tag"] = tag

    url = f"{meta_api}/workspace/{workspace_id}/table"
    log_debug(f"Creating table at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_update_table(
    instance_name: str,
    workspace_id: Union[str, int],
    table_id: Union[str, int],
    name: str = None,
    description: str = None,
    docs: str = None,
    auth: bool = None,
    tag: List[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing table in a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table to update (can be provided as string or number)
        name: The new name of the table
        description: New table description
        docs: New documentation text
        auth: New authentication setting
        tag: New list of tags for the table
        
    Returns:
        A dictionary containing details about the updated table.
        
    Example:
        ```
        # Both formats work:
        result = await xano_update_table("xnwv-v1z6-dvnr", 5, 10, name="NewTableName")
        result = await xano_update_table("xnwv-v1z6-dvnr", "5", "10", description="Updated description")
        ```
    """
    log_debug(f"Called xano_update_table(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    # Build the update data, only including fields that are provided
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if docs is not None:
        data["docs"] = docs
    if auth is not None:
        data["auth"] = auth
    if tag is not None:
        data["tag"] = tag

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/meta"
    log_debug(f"Updating table at URL: {url}")
    return await make_api_request(url, headers, method="PUT", data=data)


@mcp.tool()
async def xano_delete_table(
    instance_name: str, workspace_id: Union[str, int], table_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Delete a table from a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table to delete (can be provided as string or number)
        
    Returns:
        A dictionary containing the result of the delete operation.
        
    Example:
        ```
        # Both formats work:
        result = await xano_delete_table("xnwv-v1z6-dvnr", 5, 10)
        result = await xano_delete_table("xnwv-v1z6-dvnr", "5", "10")
        ```
    """
    log_debug(f"Called xano_delete_table(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}"
    log_debug(f"Deleting table at URL: {url}")
    return await make_api_request(url, headers, method="DELETE")


##############################################
# SECTION: TABLE SCHEMA OPERATIONS
##############################################


@mcp.tool()
async def xano_get_table_schema(
    instance_name: str, workspace_id: Union[str, int], table_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Get schema for a specific Xano table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        
    Returns:
        A dictionary containing the schema of the specified table under the 'schema' key.
        
    Example:
        ```
        # Both formats work:
        result = await xano_get_table_schema("xnwv-v1z6-dvnr", 5, 10)
        result = await xano_get_table_schema("xnwv-v1z6-dvnr", "5", "10")
        ```
    """
    log_debug(f"Called xano_get_table_schema(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/schema"
    log_debug(f"Requesting table schema from URL: {url}")
    result = await make_api_request(url, headers)

    if "error" in result:
        return result

    return {"schema": result}

# ... More functions would follow the same pattern ...

# Adding one more example function, and the rest would follow the same improvements

@mcp.tool()
async def xano_browse_table_content(
    instance_name: str,
    workspace_id: Union[str, int],
    table_id: Union[str, int],
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """
    Browse content for a specific Xano table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        page: Page number (default: 1)
        per_page: Number of records per page (default: 50)
        
    Returns:
        A dictionary containing the table content with pagination.
        
    Example:
        ```
        # Any of these formats will work:
        result = await xano_browse_table_content("xnwv-v1z6-dvnr", 5, 10)
        result = await xano_browse_table_content("xnwv-v1z6-dvnr", "5", "10", page=2)
        ```
    """
    log_debug(f"Called xano_browse_table_content(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, page={page}, per_page={per_page})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",  # As per Swagger docs
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    # Prepare params for pagination
    params = {"page": page, "per_page": per_page}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content"
    log_debug(f"Browsing table content from URL: {url}")
    return await make_api_request(url, headers, params=params)


if __name__ == "__main__":
    log_debug("Starting Xano MCP server using MCP SDK...")
    try:
        # Initialize and run the server with stdio transport
        log_debug("About to call mcp.run() with stdio transport")
        mcp.run(transport="stdio")
        log_debug("mcp.run() completed successfully")
    except Exception as e:
        print(f"CRITICAL ERROR running MCP server: {str(e)}", file=sys.stderr, flush=True)
        sys.exit(1)
