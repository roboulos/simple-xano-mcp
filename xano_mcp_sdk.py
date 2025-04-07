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

    # Use the correct Xano metadata endpoint for listing all instances
    log_debug("Retrieving instances using the Xano Meta API: /instance endpoint")
    url = f"{XANO_GLOBAL_API}/instance"
    result = await make_api_request(url, headers)

    if "error" not in result and isinstance(result, list):
        log_debug(f"Successfully retrieved {len(result)} instances")
        return {"instances": result}
    else:
        log_debug(f"Failed to retrieve instances from /instance endpoint: {result.get('error', 'Unknown error')}")
    
    # If direct method failed, check if instance name is specified in environment or arguments
    log_debug("Checking for direct instance specification...")
    
    # Check environment variable
    instance_name = os.environ.get("XANO_INSTANCE")
    if instance_name:
        log_debug(f"Found instance name in environment variable: {instance_name}")
        # Get details for the specific instance using the /instance/{name} endpoint
        instance_url = f"{XANO_GLOBAL_API}/instance/{instance_name}"
        instance_result = await make_api_request(instance_url, headers)
        
        if "error" not in instance_result:
            log_debug(f"Successfully retrieved instance details for {instance_name}")
            return {"instances": [instance_result]}
    
    # Check command line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--instance" and i + 1 < len(sys.argv):
            instance_name = sys.argv[i + 1]
            log_debug(f"Found instance name in command line arguments: {instance_name}")
            
            # Get details for the specific instance
            instance_url = f"{XANO_GLOBAL_API}/instance/{instance_name}"
            instance_result = await make_api_request(instance_url, headers)
            
            if "error" not in instance_result:
                log_debug(f"Successfully retrieved instance details for {instance_name}")
                return {"instances": [instance_result]}
    
    # If we still don't have any instances, provide a clear error
    log_debug("No instances found through any discovery method")
    return {
        "instances": [], 
        "error": "Could not discover any Xano instances. Please provide an instance name using --instance parameter or XANO_INSTANCE environment variable."
    }

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

##############################################
# SECTION: TABLE SCHEMA MANIPULATION FUNCTIONS
##############################################

@mcp.tool()
async def xano_add_field_to_schema(
    instance_name: str,
    workspace_id: Union[str, int],
    table_id: Union[str, int],
    field_name: str,
    field_type: str,
    description: str = "",
    nullable: bool = False,
    default: Any = None,
    required: bool = False,
    access: str = "public",
    sensitive: bool = False,
    style: str = "single",
    validators: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Add a new field to a table schema.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        field_name: The name of the new field
        field_type: The type of the field (e.g., "text", "int", "decimal", "boolean", "date")
        description: Field description
        nullable: Whether the field can be null
        default: Default value for the field
        required: Whether the field is required
        access: Field access level ("public", "private", "internal")
        sensitive: Whether the field contains sensitive data
        style: Field style ("single" or "list")
        validators: Validation rules specific to the field type
        
    Returns:
        A dictionary containing the updated schema information
        
    Example:
        ```
        # Add a simple text field
        result = await xano_add_field_to_schema(
            "xnwv-v1z6-dvnr", 5, 10, 
            field_name="email", 
            field_type="text"
        )
        
        # Add a numeric field with validation
        result = await xano_add_field_to_schema(
            "xnwv-v1z6-dvnr", "5", "10", 
            field_name="age", 
            field_type="int",
            required=True,
            validators={"min": 18, "max": 120}
        )
        ```
    """
    log_debug(f"Called xano_add_field_to_schema(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, field_name={field_name}, field_type={field_type})")
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

    # First, get the current schema
    current_schema_result = await xano_get_table_schema(
        instance_name, workspace_id, table_id
    )
    if "error" in current_schema_result:
        return current_schema_result

    current_schema = current_schema_result["schema"]

    # Create the new field with base properties
    new_field = {
        "name": field_name,
        "type": field_type,
        "description": description,
        "nullable": nullable,
        "required": required,
        "access": access,
        "sensitive": sensitive,
        "style": style,
    }

    # Add default value if provided
    if default is not None:
        new_field["default"] = default

    # Add validators if provided
    if validators:
        new_field["validators"] = validators

    # Add the new field to the schema
    current_schema.append(new_field)

    # Prepare data for updating schema
    data = {"schema": current_schema}

    # Update the schema
    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/schema"
    log_debug(f"Updating table schema at URL: {url}")
    return await make_api_request(url, headers, method="PUT", data=data)


@mcp.tool()
async def xano_rename_schema_field(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    old_name: str, 
    new_name: str
) -> Dict[str, Any]:
    """
    Rename a field in a table schema.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        old_name: The current name of the field
        new_name: The new name for the field
        
    Returns:
        A dictionary containing the result of the rename operation
        
    Example:
        ```
        # Rename a field
        result = await xano_rename_schema_field(
            "xnwv-v1z6-dvnr", 5, 10, 
            old_name="user_email", 
            new_name="email_address"
        )
        ```
    """
    log_debug(f"Called xano_rename_schema_field(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, old_name={old_name}, new_name={new_name})")
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

    # Prepare the rename data
    data = {"old_name": old_name, "new_name": new_name}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/schema/rename"
    log_debug(f"Renaming schema field at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_delete_field(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    field_name: str
) -> Dict[str, Any]:
    """
    Delete a field from a table schema.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        field_name: The name of the field to delete
        
    Returns:
        A dictionary containing the result of the delete operation
        
    Example:
        ```
        # Delete a field
        result = await xano_delete_field(
            "xnwv-v1z6-dvnr", 5, 10, 
            field_name="obsolete_field"
        )
        ```
    """
    log_debug(f"Called xano_delete_field(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, field_name={field_name})")
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

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/schema/{field_name}"
    log_debug(f"Deleting field schema at URL: {url}")
    return await make_api_request(url, headers, method="DELETE")


##############################################
# SECTION: TABLE INDEX OPERATIONS
##############################################


@mcp.tool()
async def xano_list_indexes(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int]
) -> Dict[str, Any]:
    """
    List all indexes for a table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        
    Returns:
        A dictionary containing all indexes defined on the table
        
    Example:
        ```
        # Get all indexes for a table
        result = await xano_list_indexes("xnwv-v1z6-dvnr", 5, 10)
        ```
    """
    log_debug(f"Called xano_list_indexes(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id})")
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

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index"
    log_debug(f"Listing indexes from URL: {url}")
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_create_btree_index(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    fields: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Create a btree index on a table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        fields: List of fields and operations for the index [{"name": "field_name", "op": "asc/desc"}]
        
    Returns:
        A dictionary containing the result of the index creation operation
        
    Example:
        ```
        # Create an index on a single field
        result = await xano_create_btree_index(
            "xnwv-v1z6-dvnr", 5, 10,
            fields=[{"name": "email", "op": "asc"}]
        )
        
        # Create a composite index on multiple fields
        result = await xano_create_btree_index(
            "xnwv-v1z6-dvnr", "5", "10",
            fields=[
                {"name": "last_name", "op": "asc"},
                {"name": "first_name", "op": "asc"}
            ]
        )
        ```
    """
    log_debug(f"Called xano_create_btree_index(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, fields={fields})")
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

    # Prepare the data for creating a btree index
    data = {"fields": fields}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/btree"
    log_debug(f"Creating btree index at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_create_unique_index(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    fields: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Create a unique index on a table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        fields: List of fields and operations for the index [{"name": "field_name", "op": "asc/desc"}]
        
    Returns:
        A dictionary containing the result of the unique index creation operation
        
    Example:
        ```
        # Create a unique index on email field
        result = await xano_create_unique_index(
            "xnwv-v1z6-dvnr", 5, 10,
            fields=[{"name": "email", "op": "asc"}]
        )
        
        # Create a composite unique index
        result = await xano_create_unique_index(
            "xnwv-v1z6-dvnr", "5", "10",
            fields=[
                {"name": "company_id", "op": "asc"},
                {"name": "employee_id", "op": "asc"}
            ]
        )
        ```
    """
    log_debug(f"Called xano_create_unique_index(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, fields={fields})")
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

    # Prepare the data for creating a unique index
    data = {"fields": fields}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/unique"
    log_debug(f"Creating unique index at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_create_search_index(
    instance_name: str,
    workspace_id: Union[str, int],
    table_id: Union[str, int],
    name: str,
    lang: str,
    fields: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create a search index on a table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        name: Name for the search index
        lang: Language for the search index (e.g., "english", "spanish", etc.)
        fields: List of fields and priorities [{"name": "field_name", "priority": 1}]
        
    Returns:
        A dictionary containing the result of the search index creation operation
        
    Example:
        ```
        # Create a search index on multiple text fields
        result = await xano_create_search_index(
            "xnwv-v1z6-dvnr", 5, 10,
            name="content_search",
            lang="english",
            fields=[
                {"name": "title", "priority": 1},
                {"name": "description", "priority": 0.5},
                {"name": "keywords", "priority": 0.8}
            ]
        )
        ```
    """
    log_debug(f"Called xano_create_search_index(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, name={name}, lang={lang})")
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

    # Prepare the data for creating a search index
    data = {"name": name, "lang": lang, "fields": fields}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/search"
    log_debug(f"Creating search index at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_delete_index(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    index_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Delete an index from a table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        index_id: The ID of the index to delete (can be provided as string or number)
        
    Returns:
        A dictionary containing the result of the index deletion operation
        
    Example:
        ```
        # Delete an index
        result = await xano_delete_index("xnwv-v1z6-dvnr", 5, 10, 15)
        ```
    """
    log_debug(f"Called xano_delete_index(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, index_id={index_id})")
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
    index_id = format_id(index_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}, index_id: {index_id}")

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/{index_id}"
    log_debug(f"Deleting index at URL: {url}")
    return await make_api_request(url, headers, method="DELETE")


##############################################
# SECTION: TABLE CONTENT OPERATIONS
##############################################


@mcp.tool()
async def xano_search_table_content(
    instance_name: str,
    workspace_id: Union[str, int],
    table_id: Union[str, int],
    search_conditions: List[Dict[str, Any]] = None,
    sort: Dict[str, str] = None,
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """
    Search table content using complex filtering.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        search_conditions: List of search conditions
        sort: Dictionary with field names as keys and "asc" or "desc" as values
        page: Page number (default: 1)
        per_page: Number of records per page (default: 50)
        
    Returns:
        A dictionary containing the search results and pagination information
        
    Example:
        ```
        # Simple search for active users
        result = await xano_search_table_content(
            "xnwv-v1z6-dvnr", 5, 10,
            search_conditions=[
                {"field": "status", "operator": "equals", "value": "active"}
            ],
            sort={"created_at": "desc"}
        )
        
        # Complex search with multiple conditions
        result = await xano_search_table_content(
            "xnwv-v1z6-dvnr", "5", "10",
            search_conditions=[
                {"field": "age", "operator": "greater_than", "value": 18},
                {"field": "subscribed", "operator": "equals", "value": true},
                {"field": "last_login", "operator": "greater_than", "value": "2023-01-01"}
            ],
            sort={"last_name": "asc", "first_name": "asc"},
            page=2,
            per_page=25
        )
        ```
    """
    log_debug(f"Called xano_search_table_content(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, page={page}, per_page={per_page})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    # Prepare the search request data
    data = {
        "page": page,
        "per_page": per_page,
        "search": search_conditions if search_conditions else [],
    }

    # Add sorting if specified
    if sort:
        data["sort"] = sort

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/search"
    log_debug(f"Searching table content at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_get_table_record(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    record_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Get a specific record from a table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        record_id: The ID of the record to retrieve (can be provided as string or number)
        
    Returns:
        A dictionary containing the record data
        
    Example:
        ```
        # Both formats work:
        result = await xano_get_table_record("xnwv-v1z6-dvnr", 5, 10, 100)
        result = await xano_get_table_record("xnwv-v1z6-dvnr", "5", "10", "100")
        ```
    """
    log_debug(f"Called xano_get_table_record(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, record_id={record_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    record_id = format_id(record_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}, record_id: {record_id}")

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/{record_id}"
    log_debug(f"Getting table record from URL: {url}")
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_create_table_record(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    record_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new record in a table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        record_data: The data for the new record
        
    Returns:
        A dictionary containing the created record data
        
    Example:
        ```
        # Create a user record
        result = await xano_create_table_record(
            "xnwv-v1z6-dvnr", 5, 10,
            record_data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "status": "active"
            }
        )
        ```
    """
    log_debug(f"Called xano_create_table_record(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content"
    log_debug(f"Creating table record at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=record_data)


@mcp.tool()
async def xano_update_table_record(
    instance_name: str,
    workspace_id: Union[str, int],
    table_id: Union[str, int],
    record_id: Union[str, int],
    record_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update an existing record in a table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        record_id: The ID of the record to update (can be provided as string or number)
        record_data: The updated data for the record
        
    Returns:
        A dictionary containing the updated record data
        
    Example:
        ```
        # Update a user's status
        result = await xano_update_table_record(
            "xnwv-v1z6-dvnr", 5, 10, 100,
            record_data={
                "status": "inactive",
                "last_updated": "2023-08-15T14:30:00Z"
            }
        )
        ```
    """
    log_debug(f"Called xano_update_table_record(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, record_id={record_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    record_id = format_id(record_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}, record_id: {record_id}")

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/{record_id}"
    log_debug(f"Updating table record at URL: {url}")
    return await make_api_request(url, headers, method="PUT", data=record_data)


@mcp.tool()
async def xano_delete_table_record(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    record_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Delete a specific record from a table.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        record_id: The ID of the record to delete (can be provided as string or number)
        
    Returns:
        A dictionary containing the result of the delete operation
        
    Example:
        ```
        # Both formats work:
        result = await xano_delete_table_record("xnwv-v1z6-dvnr", 5, 10, 100)
        result = await xano_delete_table_record("xnwv-v1z6-dvnr", "5", "10", "100")
        ```
    """
    log_debug(f"Called xano_delete_table_record(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, record_id={record_id})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    record_id = format_id(record_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}, record_id: {record_id}")

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/{record_id}"
    log_debug(f"Deleting table record at URL: {url}")
    return await make_api_request(url, headers, method="DELETE")


##############################################
# SECTION: BULK OPERATIONS
##############################################


@mcp.tool()
async def xano_bulk_create_records(
    instance_name: str,
    workspace_id: Union[str, int],
    table_id: Union[str, int],
    records: List[Dict[str, Any]],
    allow_id_field: bool = False,
) -> Dict[str, Any]:
    """
    Create multiple records in a table in a single operation.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        records: List of record data to insert
        allow_id_field: Whether to allow setting the ID field
        
    Returns:
        A dictionary containing information about the batch insertion operation
        
    Example:
        ```
        # Create multiple users at once
        result = await xano_bulk_create_records(
            "xnwv-v1z6-dvnr", 5, 10,
            records=[
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com"
                },
                {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@example.com"
                }
            ]
        )
        ```
    """
    log_debug(f"Called xano_bulk_create_records(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, records_count={len(records)})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    # Prepare the bulk insert data
    data = {"items": records, "allow_id_field": allow_id_field}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/bulk"
    log_debug(f"Bulk creating records at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_bulk_update_records(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    updates: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Update multiple records in a table in a single operation.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        updates: List of update operations, each containing row_id and updates
        
    Returns:
        A dictionary containing information about the batch update operation
        
    Example:
        ```
        # Update multiple user records
        result = await xano_bulk_update_records(
            "xnwv-v1z6-dvnr", 5, 10,
            updates=[
                {
                    "row_id": 100,
                    "updates": {
                        "status": "active",
                        "last_login": "2023-08-15T10:30:00Z"
                    }
                },
                {
                    "row_id": 101,
                    "updates": {
                        "status": "inactive",
                        "last_login": "2023-08-10T14:45:00Z"
                    }
                }
            ]
        )
        ```
    """
    log_debug(f"Called xano_bulk_update_records(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, updates_count={len(updates)})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    # Format row_ids in updates
    for update in updates:
        if "row_id" in update:
            update["row_id"] = format_id(update["row_id"])

    # Prepare the bulk update data
    data = {"items": updates}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/bulk/patch"
    log_debug(f"Bulk updating records at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_bulk_delete_records(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    record_ids: List[Union[str, int]]
) -> Dict[str, Any]:
    """
    Delete multiple records from a table in a single operation.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        record_ids: List of record IDs to delete (can be provided as strings or numbers)
        
    Returns:
        A dictionary containing information about the batch deletion operation
        
    Example:
        ```
        # Delete multiple records
        result = await xano_bulk_delete_records(
            "xnwv-v1z6-dvnr", 5, 10,
            record_ids=[100, 101, 102]
        )
        
        # Also works with string IDs
        result = await xano_bulk_delete_records(
            "xnwv-v1z6-dvnr", "5", "10",
            record_ids=["100", "101", "102"]
        )
        ```
    """
    log_debug(f"Called xano_bulk_delete_records(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, record_ids_count={len(record_ids)})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    formatted_record_ids = [format_id(record_id) for record_id in record_ids]
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    # Prepare the bulk delete data
    data = {"row_ids": formatted_record_ids}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/bulk/delete"
    log_debug(f"Bulk deleting records at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_truncate_table(
    instance_name: str, 
    workspace_id: Union[str, int], 
    table_id: Union[str, int], 
    reset: bool = False
) -> Dict[str, Any]:
    """
    Truncate a table, optionally resetting the primary key.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        table_id: The ID of the table (can be provided as string or number)
        reset: Whether to reset the primary key counter
        
    Returns:
        A dictionary containing the result of the truncate operation
        
    Example:
        ```
        # Truncate a table but keep the ID counter
        result = await xano_truncate_table("xnwv-v1z6-dvnr", 5, 10)
        
        # Truncate a table and reset the ID counter to 1
        result = await xano_truncate_table("xnwv-v1z6-dvnr", "5", "10", reset=True)
        ```
    """
    log_debug(f"Called xano_truncate_table(instance_name={instance_name}, workspace_id={workspace_id}, table_id={table_id}, reset={reset})")
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Format IDs to ensure they're proper strings
    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, table_id: {table_id}")

    # Prepare the truncate data
    data = {"reset": reset}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/truncate"
    log_debug(f"Truncating table at URL: {url}")
    return await make_api_request(url, headers, method="DELETE", data=data)


##############################################
# SECTION: FILE OPERATIONS
##############################################


@mcp.tool()
async def xano_list_files(
    instance_name: str,
    workspace_id: Union[str, int],
    page: int = 1,
    per_page: int = 50,
    search: str = None,
    access: str = None,
    sort: str = None,
    order: str = "desc",
) -> Dict[str, Any]:
    """
    List files within a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        page: Page number (default: 1)
        per_page: Number of files per page (default: 50)
        search: Search term for filtering files
        access: Filter by access level ("public" or "private")
        sort: Field to sort by ("created_at", "name", "size", "mime")
        order: Sort order ("asc" or "desc")
        
    Returns:
        A dictionary containing a list of files and pagination information
            
    Example:
        ```
        # List all files in a workspace
        result = await xano_list_files("xnwv-v1z6-dvnr", 5)
            
        # List files with filtering and sorting
        result = await xano_list_files(
                "xnwv-v1z6-dvnr", "5",
                search="report",
                access="public",
                sort="created_at",
                order="desc",
                page=2,
                per_page=25
            )
            ```
        """
    log_debug(f"Called xano_list_files(instance_name={instance_name}, workspace_id={workspace_id}, page={page}, per_page={per_page})")
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
    log_debug(f"Formatted workspace_id: {workspace_id}")

    # Prepare params
    params = {"page": page, "per_page": per_page}

    if search:
        params["search"] = search

    if access:
        params["access"] = access

    if sort:
        params["sort"] = sort
        params["order"] = order

    url = f"{meta_api}/workspace/{workspace_id}/file"
    log_debug(f"Listing files from URL: {url}")
    return await make_api_request(url, headers, params=params)
    
    
@mcp.tool()
async def xano_get_file_details(
    instance_name: str, 
    workspace_id: Union[str, int], 
    file_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Get details for a specific file.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        file_id: The ID of the file (can be provided as string or number)
        
    Returns:
        A dictionary containing details about the specified file
        
    Example:
        ```
        # Both formats work:
        result = await xano_get_file_details("xnwv-v1z6-dvnr", 5, 10)
        result = await xano_get_file_details("xnwv-v1z6-dvnr", "5", "10")
        ```
    """
    log_debug(f"Called xano_get_file_details(instance_name={instance_name}, workspace_id={workspace_id}, file_id={file_id})")
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
    file_id = format_id(file_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, file_id: {file_id}")

    url = f"{meta_api}/workspace/{workspace_id}/file/{file_id}"
    log_debug(f"Getting file details from URL: {url}")
    return await make_api_request(url, headers)
    
    
@mcp.tool()
async def xano_delete_file(
    instance_name: str, 
    workspace_id: Union[str, int], 
    file_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Delete a file from a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        file_id: The ID of the file to delete (can be provided as string or number)
        
    Returns:
        A dictionary containing the result of the delete operation
        
    Example:
        ```
        # Both formats work:
        result = await xano_delete_file("xnwv-v1z6-dvnr", 5, 10)
        result = await xano_delete_file("xnwv-v1z6-dvnr", "5", "10")
        ```
    """
    log_debug(f"Called xano_delete_file(instance_name={instance_name}, workspace_id={workspace_id}, file_id={file_id})")
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
    file_id = format_id(file_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, file_id: {file_id}")

    url = f"{meta_api}/workspace/{workspace_id}/file/{file_id}"
    log_debug(f"Deleting file at URL: {url}")
    return await make_api_request(url, headers, method="DELETE")
    
    
@mcp.tool()
async def xano_bulk_delete_files(
    instance_name: str, 
    workspace_id: Union[str, int], 
    file_ids: List[Union[str, int]]
) -> Dict[str, Any]:
    """
    Delete multiple files from a workspace in a single operation.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        file_ids: List of file IDs to delete (can be provided as strings or numbers)
        
    Returns:
        A dictionary containing the result of the bulk delete operation
        
    Example:
        ```
        # Delete multiple files at once
        result = await xano_bulk_delete_files(
            "xnwv-v1z6-dvnr", 5, 
            file_ids=[10, 11, 12]
        )
        
        # Also works with string IDs
        result = await xano_bulk_delete_files(
            "xnwv-v1z6-dvnr", "5", 
            file_ids=["10", "11", "12"]
        )
        ```
    """
    log_debug(f"Called xano_bulk_delete_files(instance_name={instance_name}, workspace_id={workspace_id}, file_ids_count={len(file_ids)})")
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
    formatted_file_ids = [format_id(file_id) for file_id in file_ids]
    
    log_debug(f"Formatted workspace_id: {workspace_id}")

    # Prepare the bulk delete data
    data = {"ids": formatted_file_ids}

    url = f"{meta_api}/workspace/{workspace_id}/file/bulk_delete"
    log_debug(f"Bulk deleting files at URL: {url}")
    return await make_api_request(url, headers, method="DELETE", data=data)
    
    
    ##############################################
    # SECTION: REQUEST HISTORY OPERATIONS
    ##############################################
    
    
@mcp.tool()
async def xano_browse_request_history(
    instance_name: str,
    workspace_id: Union[str, int],
    page: int = 1,
    per_page: int = 50,
    branch: str = None,
    api_id: Union[str, int] = None,
    query_id: Union[str, int] = None,
    include_output: bool = False,
) -> Dict[str, Any]:
    """
    Browse request history for a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        page: Page number (default: 1)
        per_page: Number of results per page (default: 50)
        branch: Filter by branch
        api_id: Filter by API ID (can be provided as string or number)
        query_id: Filter by query ID (can be provided as string or number)
        include_output: Whether to include response output
        
    Returns:
        A dictionary containing request history entries and pagination information
        
    Example:
        ```
        # Get recent request history
        result = await xano_browse_request_history("xnwv-v1z6-dvnr", 5)
        
        # Get filtered request history with response output
        result = await xano_browse_request_history(
            "xnwv-v1z6-dvnr", "5",
            branch="main",
            api_id=10,
            include_output=True,
            page=2,
            per_page=25
        )
        ```
    """
    log_debug(f"Called xano_browse_request_history(instance_name={instance_name}, workspace_id={workspace_id}, page={page}, per_page={per_page})")
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
    
    log_debug(f"Formatted workspace_id: {workspace_id}")

    # Format optional ID parameters if provided
    if api_id is not None:
        api_id = format_id(api_id)
    if query_id is not None:
        query_id = format_id(query_id)

    # Prepare params
    params = {"page": page, "per_page": per_page}

    if branch:
        params["branch"] = branch

    if api_id:
        params["api_id"] = api_id

    if query_id:
        params["query_id"] = query_id

    if include_output:
        params["include_output"] = str(include_output).lower()

    url = f"{meta_api}/workspace/{workspace_id}/request_history"
    log_debug(f"Browsing request history from URL: {url}")
    return await make_api_request(url, headers, params=params)
    
    
    ##############################################
    # SECTION: WORKSPACE IMPORT AND EXPORT
    ##############################################
    
    
@mcp.tool()
async def xano_export_workspace(
    instance_name: str, 
    workspace_id: Union[str, int], 
    branch: str = None, 
    password: str = None
) -> Dict[str, Any]:
    """
    Export a workspace to a file.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace to export (can be provided as string or number)
        branch: Branch to export (defaults to live branch if not specified)
        password: Password to encrypt the export (optional)
        
    Returns:
        A dictionary containing export information, including a download URL
        
    Example:
        ```
        # Export the live branch
        result = await xano_export_workspace("xnwv-v1z6-dvnr", 5)
        
        # Export a specific branch with password protection
        result = await xano_export_workspace(
            "xnwv-v1z6-dvnr", "5",
            branch="development",
            password="secure_password"
        )
        ```
    """
    log_debug(f"Called xano_export_workspace(instance_name={instance_name}, workspace_id={workspace_id}, branch={branch})")
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

    # Prepare export data
    data = {}
    if branch:
        data["branch"] = branch
    if password:
        data["password"] = password

    url = f"{meta_api}/workspace/{workspace_id}/export"
    log_debug(f"Exporting workspace from URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)
    
    
@mcp.tool()
async def xano_export_workspace_schema(
    instance_name: str, 
    workspace_id: Union[str, int], 
    branch: str = None, 
    password: str = None
) -> Dict[str, Any]:
    """
    Export only the schema of a workspace to a file.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        branch: Branch to export (defaults to live branch if not specified)
        password: Password to encrypt the export (optional)
        
    Returns:
        A dictionary containing export information, including a download URL
        
    Example:
        ```
        # Export only the schema of the live branch
        result = await xano_export_workspace_schema("xnwv-v1z6-dvnr", 5)
        
        # Export the schema of a specific branch with password protection
        result = await xano_export_workspace_schema(
            "xnwv-v1z6-dvnr", "5",
            branch="development",
            password="secure_password"
        )
        ```
    """
    log_debug(f"Called xano_export_workspace_schema(instance_name={instance_name}, workspace_id={workspace_id}, branch={branch})")
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

    # Prepare export data
    data = {}
    if branch:
        data["branch"] = branch
    if password:
        data["password"] = password

    url = f"{meta_api}/workspace/{workspace_id}/export-schema"
    log_debug(f"Exporting workspace schema from URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)

##############################################
# SECTION: API GROUP OPERATIONS
##############################################


@mcp.tool()
async def xano_browse_api_groups(
    instance_name: str,
    workspace_id: Union[str, int],
    branch: str = None,
    page: int = 1,
    per_page: int = 50,
    search: str = None,
    sort: str = None,
    order: str = "desc"
) -> Dict[str, Any]:
    """
    Browse API groups in a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        branch: Filter by branch name
        page: Page number (default: 1)
        per_page: Number of results per page (default: 50)
        search: Search term for filtering API groups
        sort: Field to sort by ("created_at", "updated_at", "name")
        order: Sort order ("asc" or "desc")
        
    Returns:
        A dictionary containing a list of API groups and pagination information
        
    Example:
        ```
        # List all API groups in a workspace
        result = await xano_browse_api_groups("xnwv-v1z6-dvnr", 5)
        
        # Search for API groups with pagination and sorting
        result = await xano_browse_api_groups(
            "xnwv-v1z6-dvnr", "5",
            search="auth",
            sort="name",
            order="asc",
            page=2,
            per_page=25
        )
        ```
    """
    log_debug(f"Called xano_browse_api_groups(instance_name={instance_name}, workspace_id={workspace_id}, page={page}, per_page={per_page})")
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
    log_debug(f"Formatted workspace_id: {workspace_id}")

    # Prepare params
    params = {"page": page, "per_page": per_page}

    if branch:
        params["branch"] = branch
    
    if search:
        params["search"] = search
    
    if sort:
        params["sort"] = sort
        params["order"] = order

    url = f"{meta_api}/workspace/{workspace_id}/apigroup"
    log_debug(f"Browsing API groups from URL: {url}")
    return await make_api_request(url, headers, params=params)


@mcp.tool()
async def xano_get_api_group(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Get details for a specific API group.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group (can be provided as string or number)
        
    Returns:
        A dictionary containing details about the specified API group
        
    Example:
        ```
        # Both formats work:
        result = await xano_get_api_group("xnwv-v1z6-dvnr", 5, 10)
        result = await xano_get_api_group("xnwv-v1z6-dvnr", "5", "10")
        ```
    """
    log_debug(f"Called xano_get_api_group(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id})")
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
    apigroup_id = format_id(apigroup_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}")

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}"
    log_debug(f"Getting API group details from URL: {url}")
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_create_api_group(
    instance_name: str,
    workspace_id: Union[str, int],
    name: str,
    description: str = "",
    docs: str = "",
    branch: str = None,
    swagger: bool = True,
    tag: List[str] = None
) -> Dict[str, Any]:
    """
    Create a new API group in a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        name: The name of the new API group
        description: API group description
        docs: Documentation text
        branch: Branch to create the API group in (defaults to current branch)
        swagger: Whether to enable Swagger documentation
        tag: List of tags for the API group
        
    Returns:
        A dictionary containing details about the newly created API group
        
    Example:
        ```
        # Create a simple API group
        result = await xano_create_api_group(
            "xnwv-v1z6-dvnr", 5, 
            name="Authentication APIs"
        )
        
        # Create an API group with additional details
        result = await xano_create_api_group(
            "xnwv-v1z6-dvnr", "5",
            name="User Management",
            description="APIs for user management operations",
            docs="Use these endpoints to create, update, and delete users",
            branch="development",
            tag=["auth", "users"]
        )
        ```
    """
    log_debug(f"Called xano_create_api_group(instance_name={instance_name}, workspace_id={workspace_id}, name={name})")
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

    # Prepare the API group creation data
    data = {
        "name": name,
        "description": description,
        "docs": docs,
        "swagger": swagger
    }
    
    if branch:
        data["branch"] = branch
        
    if tag:
        data["tag"] = tag

    url = f"{meta_api}/workspace/{workspace_id}/apigroup"
    log_debug(f"Creating API group at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_update_api_group(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int],
    name: str = None,
    description: str = None,
    docs: str = None,
    swagger: bool = None,
    tag: List[str] = None
) -> Dict[str, Any]:
    """
    Update an existing API group in a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group to update (can be provided as string or number)
        name: The new name of the API group
        description: New API group description
        docs: New documentation text
        swagger: Whether to enable Swagger documentation
        tag: New list of tags for the API group
        
    Returns:
        A dictionary containing details about the updated API group
        
    Example:
        ```
        # Update the name of an API group
        result = await xano_update_api_group(
            "xnwv-v1z6-dvnr", 5, 10,
            name="Updated API Group Name"
        )
        
        # Update multiple properties
        result = await xano_update_api_group(
            "xnwv-v1z6-dvnr", "5", "10",
            description="Updated description",
            docs="New documentation",
            tag=["updated", "api"]
        )
        ```
    """
    log_debug(f"Called xano_update_api_group(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id})")
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
    apigroup_id = format_id(apigroup_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}")

    # Build the update data, only including fields that are provided
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if docs is not None:
        data["docs"] = docs
    if swagger is not None:
        data["swagger"] = swagger
    if tag is not None:
        data["tag"] = tag

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}"
    log_debug(f"Updating API group at URL: {url}")
    return await make_api_request(url, headers, method="PUT", data=data)


@mcp.tool()
async def xano_delete_api_group(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Delete an API group from a workspace.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group to delete (can be provided as string or number)
        
    Returns:
        A dictionary containing the result of the delete operation
        
    Example:
        ```
        # Both formats work:
        result = await xano_delete_api_group("xnwv-v1z6-dvnr", 5, 10)
        result = await xano_delete_api_group("xnwv-v1z6-dvnr", "5", "10")
        ```
    """
    log_debug(f"Called xano_delete_api_group(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id})")
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
    apigroup_id = format_id(apigroup_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}")

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}"
    log_debug(f"Deleting API group at URL: {url}")
    return await make_api_request(url, headers, method="DELETE")


@mcp.tool()
async def xano_update_api_group_security(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int],
    guid: str,
    canonical: str
) -> Dict[str, Any]:
    """
    Update the security settings for an API group.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group (can be provided as string or number)
        guid: The new GUID for the API group
        canonical: The canonical URL for the API group
        
    Returns:
        A dictionary containing the updated API group details
        
    Example:
        ```
        # Update security settings
        result = await xano_update_api_group_security(
            "xnwv-v1z6-dvnr", 5, 10,
            guid="new-guid-value",
            canonical="https://api.example.com/v1"
        )
        ```
    """
    log_debug(f"Called xano_update_api_group_security(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id})")
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
    apigroup_id = format_id(apigroup_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}")

    # Prepare the security settings data
    data = {
        "guid": guid,
        "canonical": canonical
    }

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}/security"
    log_debug(f"Updating API group security settings at URL: {url}")
    return await make_api_request(url, headers, method="PUT", data=data)


@mcp.tool()
async def xano_browse_apis_in_group(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int],
    page: int = 1,
    per_page: int = 50,
    search: str = None,
    sort: str = None,
    order: str = "desc"
) -> Dict[str, Any]:
    """
    Browse APIs within a specific API group.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group (can be provided as string or number)
        page: Page number (default: 1)
        per_page: Number of APIs per page (default: 50)
        search: Search term for filtering APIs
        sort: Field to sort by ("created_at", "updated_at", "name")
        order: Sort order ("asc" or "desc")
        
    Returns:
        A dictionary containing a list of APIs and pagination information
        
    Example:
        ```
        # List all APIs in a group
        result = await xano_browse_apis_in_group("xnwv-v1z6-dvnr", 5, 10)
        
        # Search for APIs with sorting
        result = await xano_browse_apis_in_group(
            "xnwv-v1z6-dvnr", "5", "10",
            search="user",
            sort="name",
            order="asc",
            page=2,
            per_page=25
        )
        ```
    """
    log_debug(f"Called xano_browse_apis_in_group(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id}, page={page}, per_page={per_page})")
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
    apigroup_id = format_id(apigroup_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}")

    # Prepare params
    params = {"page": page, "per_page": per_page}
    
    if search:
        params["search"] = search
    
    if sort:
        params["sort"] = sort
        params["order"] = order

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}/api"
    log_debug(f"Browsing APIs in group from URL: {url}")
    return await make_api_request(url, headers, params=params)


@mcp.tool()
async def xano_get_api(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int],
    api_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Get details for a specific API.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group (can be provided as string or number)
        api_id: The ID of the API (can be provided as string or number)
        
    Returns:
        A dictionary containing details about the specified API
        
    Example:
        ```
        # All of these formats work:
        result = await xano_get_api("xnwv-v1z6-dvnr", 5, 10, 15)
        result = await xano_get_api("xnwv-v1z6-dvnr", "5", "10", "15")
        ```
    """
    log_debug(f"Called xano_get_api(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id}, api_id={api_id})")
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
    apigroup_id = format_id(apigroup_id)
    api_id = format_id(api_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}, api_id: {api_id}")

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}/api/{api_id}"
    log_debug(f"Getting API details from URL: {url}")
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_create_api(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int],
    name: str,
    description: str = "",
    docs: str = "",
    verb: str = "GET",
    tag: List[str] = None
) -> Dict[str, Any]:
    """
    Create a new API within an API group.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group (can be provided as string or number)
        name: The name of the new API
        description: API description
        docs: Documentation text
        verb: HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD)
        tag: List of tags for the API
        
    Returns:
        A dictionary containing details about the newly created API
        
    Example:
        ```
        # Create a GET API
        result = await xano_create_api(
            "xnwv-v1z6-dvnr", 5, 10,
            name="Get User Profile",
            verb="GET"
        )
        
        # Create a POST API with more details
        result = await xano_create_api(
            "xnwv-v1z6-dvnr", "5", "10",
            name="Create User",
            description="Creates a new user in the system",
            docs="Use this endpoint to register new users",
            verb="POST",
            tag=["users", "auth"]
        )
        ```
    """
    log_debug(f"Called xano_create_api(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id}, name={name}, verb={verb})")
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
    apigroup_id = format_id(apigroup_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}")

    # Prepare the API creation data
    data = {
        "name": name,
        "description": description,
        "docs": docs,
        "verb": verb
    }
    
    if tag:
        data["tag"] = tag

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}/api"
    log_debug(f"Creating API at URL: {url}")
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_update_api(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int],
    api_id: Union[str, int],
    name: str = None,
    description: str = None,
    docs: str = None,
    verb: str = None,
    auth: Dict[str, Any] = None,
    tag: List[str] = None,
    cache: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Update an existing API.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group (can be provided as string or number)
        api_id: The ID of the API to update (can be provided as string or number)
        name: The new name of the API
        description: New API description
        docs: New documentation text
        verb: New HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD)
        auth: Authentication settings
        tag: New list of tags for the API
        cache: Cache settings
        
    Returns:
        A dictionary containing the result of the update operation
        
    Example:
        ```
        # Update the name of an API
        result = await xano_update_api(
            "xnwv-v1z6-dvnr", 5, 10, 15,
            name="Updated API Name"
        )
        
        # Update multiple properties
        result = await xano_update_api(
            "xnwv-v1z6-dvnr", "5", "10", "15",
            description="Updated description",
            docs="New documentation",
            verb="PUT",
            tag=["updated", "api"],
            cache={"active": True, "ttl": 300}
        )
        ```
    """
    log_debug(f"Called xano_update_api(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id}, api_id={api_id})")
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
    apigroup_id = format_id(apigroup_id)
    api_id = format_id(api_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}, api_id: {api_id}")

    # Build the update data, only including fields that are provided
    data = {}
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if docs is not None:
        data["docs"] = docs
    if verb is not None:
        data["verb"] = verb
    if auth is not None:
        data["auth"] = auth
    if tag is not None:
        data["tag"] = tag
    if cache is not None:
        data["cache"] = cache

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}/api/{api_id}"
    log_debug(f"Updating API at URL: {url}")
    return await make_api_request(url, headers, method="PUT", data=data)


@mcp.tool()
async def xano_delete_api(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int],
    api_id: Union[str, int]
) -> Dict[str, Any]:
    """
    Delete an API from an API group.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group (can be provided as string or number)
        api_id: The ID of the API to delete (can be provided as string or number)
        
    Returns:
        A dictionary containing the result of the delete operation
        
    Example:
        ```
        # All formats work:
        result = await xano_delete_api("xnwv-v1z6-dvnr", 5, 10, 15)
        result = await xano_delete_api("xnwv-v1z6-dvnr", "5", "10", "15")
        ```
    """
    log_debug(f"Called xano_delete_api(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id}, api_id={api_id})")
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
    apigroup_id = format_id(apigroup_id)
    api_id = format_id(api_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}, api_id: {api_id}")

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}/api/{api_id}"
    log_debug(f"Deleting API at URL: {url}")
    return await make_api_request(url, headers, method="DELETE")


@mcp.tool()
async def xano_update_api_security(
    instance_name: str,
    workspace_id: Union[str, int],
    apigroup_id: Union[str, int],
    api_id: Union[str, int],
    guid: str
) -> Dict[str, Any]:
    """
    Update the security settings for an API.

    Args:
        instance_name: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")
        workspace_id: The ID of the workspace (can be provided as string or number)
        apigroup_id: The ID of the API group (can be provided as string or number)
        api_id: The ID of the API (can be provided as string or number)
        guid: The new GUID for the API
        
    Returns:
        A dictionary containing the result of the update operation
        
    Example:
        ```
        # Update API security settings
        result = await xano_update_api_security(
            "xnwv-v1z6-dvnr", 5, 10, 15,
            guid="new-api-guid-value"
        )
        ```
    """
    log_debug(f"Called xano_update_api_security(instance_name={instance_name}, workspace_id={workspace_id}, apigroup_id={apigroup_id}, api_id={api_id})")
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
    apigroup_id = format_id(apigroup_id)
    api_id = format_id(api_id)
    
    log_debug(f"Formatted workspace_id: {workspace_id}, apigroup_id: {apigroup_id}, api_id: {api_id}")

    # Prepare the security settings data
    data = {"guid": guid}

    url = f"{meta_api}/workspace/{workspace_id}/apigroup/{apigroup_id}/api/{api_id}/security"
    log_debug(f"Updating API security settings at URL: {url}")
    return await make_api_request(url, headers, method="PUT", data=data)

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
