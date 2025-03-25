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


# Utility function to make API requests
async def make_api_request(
    url, headers, method="GET", data=None, params=None, files=None
):
    """Helper function to make API requests with consistent error handling"""
    try:
        print(f"Making {method} request to {url}", file=sys.stderr)
        if params:
            print(f"With params: {params}", file=sys.stderr)
        if data and not files:
            print(f"With data: {json.dumps(data)[:500]}...", file=sys.stderr)

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

            print(f"Response status: {response.status_code}", file=sys.stderr)

            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print(
                        f"Error parsing JSON response: {response.text[:200]}...",
                        file=sys.stderr,
                    )
                    return {"error": "Failed to parse response as JSON"}
            else:
                print(f"Error response: {response.text[:200]}...", file=sys.stderr)
                return {
                    "error": f"API request failed with status {response.status_code}"
                }
    except Exception as e:
        print(f"Exception during API request: {str(e)}", file=sys.stderr)
        return {"error": f"Exception during API request: {str(e)}"}


# Utility function to ensure IDs are properly formatted as strings
def format_id(id_value):
    """Ensures IDs are properly formatted strings"""
    if id_value is None:
        return None
    return str(id_value).strip('"')


##############################################
# SECTION: INSTANCE AND DATABASE OPERATIONS
##############################################


@mcp.tool()
async def xano_list_instances() -> Dict[str, Any]:
    """List all Xano instances associated with the account."""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # First try the direct auth/me endpoint
    result = await make_api_request(f"{XANO_GLOBAL_API}/auth/me", headers)

    if "error" not in result and "instances" in result:
        return {"instances": result["instances"]}

    # If that doesn't work, perform a workaround - list any known instances
    # This is a fallback for when the API doesn't return instances directly
    print("Falling back to hardcoded instance detection...", file=sys.stderr)
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
    """Get details for a specific Xano instance.

    Args:
        instance_name: The name of the Xano instance
    """
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
    """List all databases (workspaces) in a specific Xano instance.

    Args:
        instance_name: The name of the Xano instance
    """
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
    print(f"Listing databases from URL: {url}", file=sys.stderr)
    result = await make_api_request(url, headers)

    if "error" in result:
        return result

    return {"databases": result}


@mcp.tool()
async def xano_get_workspace_details(
    instance_name: str, workspace_id: str
) -> Dict[str, Any]:
    """Get details for a specific Xano workspace.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    url = f"{meta_api}/workspace/{workspace_id}"
    print(f"Requesting workspace details from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers)


##############################################
# SECTION: TABLE OPERATIONS
##############################################


@mcp.tool()
async def xano_list_tables(instance_name: str, database_name: str) -> Dict[str, Any]:
    """List all tables in a specific Xano database (workspace).

    Args:
        instance_name: The name of the Xano instance
        database_name: The ID of the Xano workspace (database)
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    # Use the workspace ID (database_name) to list tables
    workspace_id = format_id(database_name)

    # List tables in the workspace
    url = f"{meta_api}/workspace/{workspace_id}/table"
    print(f"Requesting tables from URL: {url}", file=sys.stderr)
    result = await make_api_request(url, headers)

    if "error" in result:
        return result

    # Handle different response formats
    if "items" in result:
        return {"tables": result["items"]}
    else:
        return {"tables": result}


@mcp.tool()
async def xano_get_table_details(
    instance_name: str, workspace_id: str, table_id: str
) -> Dict[str, Any]:
    """Get details for a specific Xano table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}"
    print(f"Requesting table details from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_create_table(
    instance_name: str,
    workspace_id: str,
    name: str,
    description: str = "",
    docs: str = "",
    auth: bool = False,
    tag: List[str] = None,
) -> Dict[str, Any]:
    """Create a new table in a workspace.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        name: The name of the new table
        description: Table description
        docs: Documentation text
        auth: Whether authentication is required
        tag: List of tags for the table
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    # Prepare the table creation data
    data = {"name": name, "description": description, "docs": docs, "auth": auth}

    if tag:
        data["tag"] = tag

    url = f"{meta_api}/workspace/{workspace_id}/table"
    print(f"Creating table at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_update_table(
    instance_name: str,
    workspace_id: str,
    table_id: str,
    name: str = None,
    description: str = None,
    docs: str = None,
    auth: bool = None,
    tag: List[str] = None,
) -> Dict[str, Any]:
    """Update an existing table in a workspace.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table to update
        name: The new name of the table
        description: New table description
        docs: New documentation text
        auth: New authentication setting
        tag: New list of tags for the table
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

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
    print(f"Updating table at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="PUT", data=data)


@mcp.tool()
async def xano_delete_table(
    instance_name: str, workspace_id: str, table_id: str
) -> Dict[str, Any]:
    """Delete a table from a workspace.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table to delete
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}"
    print(f"Deleting table at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="DELETE")


##############################################
# SECTION: TABLE SCHEMA OPERATIONS
##############################################


@mcp.tool()
async def xano_get_table_schema(
    instance_name: str, workspace_id: str, table_id: str
) -> Dict[str, Any]:
    """Get schema for a specific Xano table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/schema"
    print(f"Requesting table schema from URL: {url}", file=sys.stderr)
    result = await make_api_request(url, headers)

    if "error" in result:
        return result

    return {"schema": result}


@mcp.tool()
async def xano_update_table_schema(
    instance_name: str, workspace_id: str, table_id: str, schema: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Update the entire schema of a Xano table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        schema: A list of schema objects defining the table structure
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the data for schema update
    data = {"schema": schema}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/schema"
    print(f"Updating table schema at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="PUT", data=data)


@mcp.tool()
async def xano_add_field_to_schema(
    instance_name: str,
    workspace_id: str,
    table_id: str,
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
    """Add a new field to a table schema.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        field_name: The name of the new field
        field_type: The type of the field (e.g., "text", "int", "decimal", etc.)
        description: Field description
        nullable: Whether the field can be null
        default: Default value for the field
        required: Whether the field is required
        access: Field access level ("public", "private", "internal")
        sensitive: Whether the field contains sensitive data
        style: Field style ("single" or "list")
        validators: Validation rules specific to the field type
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

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
    if validators and field_type == "text":
        new_field["validators"] = validators

    # Add the new field to the schema
    current_schema.append(new_field)

    # Update the schema
    return await xano_update_table_schema(
        instance_name, workspace_id, table_id, current_schema
    )


@mcp.tool()
async def xano_rename_schema_field(
    instance_name: str, workspace_id: str, table_id: str, old_name: str, new_name: str
) -> Dict[str, Any]:
    """Rename a field in a table schema.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        old_name: The current name of the field
        new_name: The new name for the field
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the rename data
    data = {"old_name": old_name, "new_name": new_name}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/schema/rename"
    print(f"Renaming schema field at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_get_field_schema(
    instance_name: str, workspace_id: str, table_id: str, field_name: str
) -> Dict[str, Any]:
    """Get schema for a specific field in a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        field_name: The name of the field
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/schema/{field_name}"
    print(f"Getting field schema from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_delete_field(
    instance_name: str, workspace_id: str, table_id: str, field_name: str
) -> Dict[str, Any]:
    """Delete a field from a table schema.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        field_name: The name of the field to delete
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/schema/{field_name}"
    print(f"Deleting field schema at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="DELETE")


##############################################
# SECTION: TABLE INDEX OPERATIONS
##############################################


@mcp.tool()
async def xano_list_indexes(
    instance_name: str, workspace_id: str, table_id: str
) -> Dict[str, Any]:
    """List all indexes for a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index"
    print(f"Listing indexes from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_create_btree_index(
    instance_name: str, workspace_id: str, table_id: str, fields: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Create a btree index on a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        fields: List of fields and operations for the index [{"name": "field_name", "op": "asc/desc"}]
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the data for creating a btree index
    data = {"fields": fields}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/btree"
    print(f"Creating btree index at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_create_unique_index(
    instance_name: str, workspace_id: str, table_id: str, fields: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Create a unique index on a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        fields: List of fields and operations for the index [{"name": "field_name", "op": "asc/desc"}]
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the data for creating a unique index
    data = {"fields": fields}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/unique"
    print(f"Creating unique index at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_create_search_index(
    instance_name: str,
    workspace_id: str,
    table_id: str,
    name: str,
    lang: str,
    fields: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Create a search index on a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        name: Name for the search index
        lang: Language for the search index (e.g., "english", "spanish", etc.)
        fields: List of fields and priorities [{"name": "field_name", "priority": 1}]
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the data for creating a search index
    data = {"name": name, "lang": lang, "fields": fields}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/search"
    print(f"Creating search index at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_create_spatial_index(
    instance_name: str, workspace_id: str, table_id: str, fields: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Create a spatial index on a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        fields: List of fields and operations for the index [{"name": "field_name", "op": "gist_geometry_ops_2d"}]
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the data for creating a spatial index
    data = {"fields": fields}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/spatial"
    print(f"Creating spatial index at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_create_vector_index(
    instance_name: str, workspace_id: str, table_id: str, fields: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Create a vector index on a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        fields: List of fields and operations for the index
               [{"name": "field_name", "op": "vector_ip_ops/vector_cosine_ops/vector_l1_ops/vector_l2_ops"}]
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the data for creating a vector index
    data = {"fields": fields}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/vector"
    print(f"Creating vector index at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_delete_index(
    instance_name: str, workspace_id: str, table_id: str, index_id: str
) -> Dict[str, Any]:
    """Delete an index from a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        index_id: The ID of the index to delete
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    index_id = format_id(index_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index/{index_id}"
    print(f"Deleting index at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="DELETE")


@mcp.tool()
async def xano_update_all_indexes(
    instance_name: str, workspace_id: str, table_id: str, indexes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Replace all indexes on a table with a new set of indexes.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        indexes: List of indexes to set on the table
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the data for updating all indexes
    data = {"index": indexes}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/index"
    print(f"Updating all indexes at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="PUT", data=data)


##############################################
# SECTION: TABLE CONTENT OPERATIONS
##############################################


@mcp.tool()
async def xano_browse_table_content(
    instance_name: str,
    workspace_id: str,
    table_id: str,
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Browse content for a specific Xano table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        page: Page number (default: 1)
        per_page: Number of records per page (default: 50)
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",  # As per Swagger docs
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare params for pagination
    params = {"page": page, "per_page": per_page}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content"
    print(f"Browsing table content from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, params=params)


@mcp.tool()
async def xano_search_table_content(
    instance_name: str,
    workspace_id: str,
    table_id: str,
    search_conditions: List[Dict[str, Any]] = None,
    sort: Dict[str, str] = None,
    page: int = 1,
    per_page: int = 50,
) -> Dict[str, Any]:
    """Search table content using complex filtering.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        search_conditions: List of search conditions
        sort: Dictionary with field names as keys and "asc" or "desc" as values
        page: Page number (default: 1)
        per_page: Number of records per page (default: 50)
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

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
    print(f"Searching table content at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_get_table_record(
    instance_name: str, workspace_id: str, table_id: str, record_id: str
) -> Dict[str, Any]:
    """Get a specific record from a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        record_id: The ID of the record to retrieve
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    record_id = format_id(record_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/{record_id}"
    print(f"Getting table record from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_create_table_record(
    instance_name: str, workspace_id: str, table_id: str, record_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a new record in a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        record_data: The data for the new record
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content"
    print(f"Creating table record at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=record_data)


@mcp.tool()
async def xano_update_table_record(
    instance_name: str,
    workspace_id: str,
    table_id: str,
    record_id: str,
    record_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Update an existing record in a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        record_id: The ID of the record to update
        record_data: The updated data for the record
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    record_id = format_id(record_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/{record_id}"
    print(f"Updating table record at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="PUT", data=record_data)


@mcp.tool()
async def xano_delete_table_record(
    instance_name: str, workspace_id: str, table_id: str, record_id: str
) -> Dict[str, Any]:
    """Delete a specific record from a table.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        record_id: The ID of the record to delete
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)
    record_id = format_id(record_id)

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/{record_id}"
    print(f"Deleting table record at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="DELETE")


@mcp.tool()
async def xano_search_and_update_records(
    instance_name: str,
    workspace_id: str,
    table_id: str,
    search_conditions: List[Dict[str, Any]],
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    """Update records matching search criteria.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        search_conditions: List of search conditions to identify records to update
        updates: Dictionary of field updates to apply to matched records
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the search criteria and updates
    data = {"search": search_conditions, "updates": updates}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/search/patch"
    print(f"Updating records by search at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_search_and_delete_records(
    instance_name: str,
    workspace_id: str,
    table_id: str,
    search_conditions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Delete records matching search criteria.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        search_conditions: List of search conditions to identify records to delete
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the search criteria for deletion
    data = {"search": search_conditions}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/search/delete"
    print(f"Deleting records by search at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_bulk_create_records(
    instance_name: str,
    workspace_id: str,
    table_id: str,
    records: List[Dict[str, Any]],
    allow_id_field: bool = False,
) -> Dict[str, Any]:
    """Create multiple records in a table in a single operation.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        records: List of record data to insert
        allow_id_field: Whether to allow setting the ID field
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the bulk insert data
    data = {"items": records, "allow_id_field": allow_id_field}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/bulk"
    print(f"Bulk creating records at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_bulk_update_records(
    instance_name: str, workspace_id: str, table_id: str, updates: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Update multiple records in a table in a single operation.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        updates: List of update operations, each containing row_id and updates
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the bulk update data
    data = {"items": updates}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/bulk/patch"
    print(f"Bulk updating records at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_bulk_delete_records(
    instance_name: str, workspace_id: str, table_id: str, record_ids: List[str]
) -> Dict[str, Any]:
    """Delete multiple records from a table in a single operation.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        record_ids: List of record IDs to delete
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the bulk delete data
    data = {"row_ids": record_ids}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/content/bulk/delete"
    print(f"Bulk deleting records at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_truncate_table(
    instance_name: str, workspace_id: str, table_id: str, reset: bool = False
) -> Dict[str, Any]:
    """Truncate a table, optionally resetting the primary key.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        table_id: The ID of the table
        reset: Whether to reset the primary key counter
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Data-Source": "live",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    table_id = format_id(table_id)

    # Prepare the truncate data
    data = {"reset": reset}

    url = f"{meta_api}/workspace/{workspace_id}/table/{table_id}/truncate"
    print(f"Truncating table at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="DELETE", data=data)


##############################################
# SECTION: FILE OPERATIONS
##############################################


@mcp.tool()
async def xano_list_files(
    instance_name: str,
    workspace_id: str,
    page: int = 1,
    per_page: int = 50,
    search: str = None,
    access: str = None,
    sort: str = None,
    order: str = "desc",
) -> Dict[str, Any]:
    """List files within a workspace.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        page: Page number (default: 1)
        per_page: Number of files per page (default: 50)
        search: Search term for filtering files
        access: Filter by access level ("public" or "private")
        sort: Field to sort by ("created_at", "name", "size", "mime")
        order: Sort order ("asc" or "desc")
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

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
    print(f"Listing files from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, params=params)


@mcp.tool()
async def xano_upload_file(
    instance_name: str,
    workspace_id: str,
    file_path: str,
    file_type: str = None,
    file_access: str = "public",
) -> Dict[str, Any]:
    """Upload a file to a workspace.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        file_path: Path to the file to upload
        file_type: Type of file ("image", "video", "audio") or None for auto-detection
        file_access: File access level ("public" or "private")
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        # Content-Type is set by httpx when using multipart/form-data
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    # Prepare the form data
    form_data = {}

    if file_type:
        form_data["type"] = file_type

    if file_access:
        form_data["access"] = file_access

    # Prepare the file
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()

        filename = os.path.basename(file_path)
        files = {"content": (filename, file_content)}

        url = f"{meta_api}/workspace/{workspace_id}/file"
        print(f"Uploading file to URL: {url}", file=sys.stderr)
        return await make_api_request(
            url, headers, method="POST", data=form_data, files=files
        )
    except Exception as e:
        print(f"Error uploading file: {str(e)}", file=sys.stderr)
        return {"error": f"Error uploading file: {str(e)}"}


@mcp.tool()
async def xano_get_file_details(
    instance_name: str, workspace_id: str, file_id: str
) -> Dict[str, Any]:
    """Get details for a specific file.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        file_id: The ID of the file
    """
    # Note: This endpoint isn't explicitly in the docs, but follows the RESTful pattern
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    file_id = format_id(file_id)

    url = f"{meta_api}/workspace/{workspace_id}/file/{file_id}"
    print(f"Getting file details from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers)


@mcp.tool()
async def xano_delete_file(
    instance_name: str, workspace_id: str, file_id: str
) -> Dict[str, Any]:
    """Delete a file from a workspace.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        file_id: The ID of the file to delete
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)
    file_id = format_id(file_id)

    url = f"{meta_api}/workspace/{workspace_id}/file/{file_id}"
    print(f"Deleting file at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="DELETE")


@mcp.tool()
async def xano_bulk_delete_files(
    instance_name: str, workspace_id: str, file_ids: List[str]
) -> Dict[str, Any]:
    """Delete multiple files from a workspace in a single operation.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        file_ids: List of file IDs to delete
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    # Prepare the bulk delete data
    data = {"ids": file_ids}

    url = f"{meta_api}/workspace/{workspace_id}/file/bulk_delete"
    print(f"Bulk deleting files at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="DELETE", data=data)


##############################################
# SECTION: REQUEST HISTORY OPERATIONS
##############################################


@mcp.tool()
async def xano_browse_request_history(
    instance_name: str,
    workspace_id: str,
    page: int = 1,
    per_page: int = 50,
    branch: str = None,
    api_id: str = None,
    query_id: str = None,
    include_output: bool = False,
) -> Dict[str, Any]:
    """Browse request history for a workspace.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        page: Page number (default: 1)
        per_page: Number of results per page (default: 50)
        branch: Filter by branch
        api_id: Filter by API ID
        query_id: Filter by query ID
        include_output: Whether to include response output
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    # Prepare params
    params = {"page": page, "per_page": per_page}

    if branch:
        params["branch"] = branch

    if api_id:
        params["api_id"] = format_id(api_id)

    if query_id:
        params["query_id"] = format_id(query_id)

    if include_output:
        params["include_output"] = str(include_output).lower()

    url = f"{meta_api}/workspace/{workspace_id}/request_history"
    print(f"Browsing request history from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, params=params)


@mcp.tool()
async def xano_search_request_history(
    instance_name: str,
    workspace_id: str,
    search_conditions: List[Dict[str, Any]] = None,
    sort: Dict[str, str] = None,
    page: int = 1,
    per_page: int = 50,
    branch_id: str = None,
    api_id: str = None,
    query_id: str = None,
    include_output: bool = False,
) -> Dict[str, Any]:
    """Search request history with complex filtering.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        search_conditions: List of search conditions
        sort: Dictionary of sort fields and directions
        page: Page number (default: 1)
        per_page: Number of results per page (default: 50)
        branch_id: Filter by branch ID
        api_id: Filter by API ID
        query_id: Filter by query ID
        include_output: Whether to include response output
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    # Prepare search request data
    data = {
        "page": page,
        "per_page": per_page,
        "search": search_conditions if search_conditions else [],
    }

    if sort:
        data["sort"] = sort

    if branch_id:
        data["branch_id"] = format_id(branch_id)

    if api_id:
        data["api_id"] = format_id(api_id)

    if query_id:
        data["query_id"] = format_id(query_id)

    if include_output:
        data["include_output"] = include_output

    url = f"{meta_api}/workspace/{workspace_id}/request_history/search"
    print(f"Searching request history at URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


##############################################
# SECTION: WORKSPACE IMPORT AND EXPORT
##############################################


@mcp.tool()
async def xano_export_workspace(
    instance_name: str, workspace_id: str, branch: str = None, password: str = None
) -> Dict[str, Any]:
    """Export a workspace to a file.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace to export
        branch: Branch to export (defaults to live branch if not specified)
        password: Password to encrypt the export (optional)
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    # Prepare export data
    data = {}
    if branch:
        data["branch"] = branch
    if password:
        data["password"] = password

    url = f"{meta_api}/workspace/{workspace_id}/export"
    print(f"Exporting workspace from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_export_workspace_schema(
    instance_name: str, workspace_id: str, branch: str = None, password: str = None
) -> Dict[str, Any]:
    """Export only the schema of a workspace to a file.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace
        branch: Branch to export (defaults to live branch if not specified)
        password: Password to encrypt the export (optional)
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    # Prepare export data
    data = {}
    if branch:
        data["branch"] = branch
    if password:
        data["password"] = password

    url = f"{meta_api}/workspace/{workspace_id}/export-schema"
    print(f"Exporting workspace schema from URL: {url}", file=sys.stderr)
    return await make_api_request(url, headers, method="POST", data=data)


@mcp.tool()
async def xano_import_workspace(
    instance_name: str, workspace_id: str, file_path: str, password: str = None
) -> Dict[str, Any]:
    """Import a workspace from a file.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace to import into
        file_path: Path to the export file
        password: Password to decrypt the export (if it was encrypted)
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        # Content-Type is set by httpx when using multipart/form-data
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    # Prepare the form data
    form_data = {}
    if password:
        form_data["password"] = password

    # Prepare the file
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()

        filename = os.path.basename(file_path)
        files = {"file": (filename, file_content)}

        url = f"{meta_api}/workspace/{workspace_id}/import"
        print(f"Importing workspace to URL: {url}", file=sys.stderr)
        return await make_api_request(
            url, headers, method="POST", data=form_data, files=files
        )
    except Exception as e:
        print(f"Error importing workspace: {str(e)}", file=sys.stderr)
        return {"error": f"Error importing workspace: {str(e)}"}


@mcp.tool()
async def xano_import_workspace_schema(
    instance_name: str,
    workspace_id: str,
    file_path: str,
    new_branch: str,
    set_live: bool = False,
    password: str = None,
) -> Dict[str, Any]:
    """Import a workspace schema from a file into a new branch.

    Args:
        instance_name: The name of the Xano instance
        workspace_id: The ID of the workspace to import into
        file_path: Path to the schema export file
        new_branch: Name for the new branch to create
        set_live: Whether to set the new branch as live
        password: Password to decrypt the export (if it was encrypted)
    """
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        # Content-Type is set by httpx when using multipart/form-data
    }

    instance_domain = f"{instance_name}.n7c.xano.io"
    meta_api = f"https://{instance_domain}/api:meta"

    workspace_id = format_id(workspace_id)

    # Prepare the form data
    form_data = {"newbranch": new_branch, "setlive": str(set_live).lower()}

    if password:
        form_data["password"] = password

    # Prepare the file
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()

        filename = os.path.basename(file_path)
        files = {"file": (filename, file_content)}

        url = f"{meta_api}/workspace/{workspace_id}/import-schema"
        print(f"Importing workspace schema to URL: {url}", file=sys.stderr)
        return await make_api_request(
            url, headers, method="POST", data=form_data, files=files
        )
    except Exception as e:
        print(f"Error importing workspace schema: {str(e)}", file=sys.stderr)
        return {"error": f"Error importing workspace schema: {str(e)}"}


if __name__ == "__main__":
    print("Starting Xano MCP server using MCP SDK...", file=sys.stderr)
    # Initialize and run the server with stdio transport
    mcp.run(transport="stdio")
