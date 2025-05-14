# Xano MCP Python SDK - Available Tools

This document provides detailed information about all the tools available in the Xano MCP Python SDK.

## Instance Management

### `xano_list_instances`
Lists all Xano instances associated with your account.

**Example:**
```python
result = await xano_list_instances()
# Returns: {"instances": [{"name": "instance-name", ...}]}
```

### `xano_get_instance_details`
Get details for a specific Xano instance.

**Parameters:**
- `instance_name`: The name of the Xano instance (e.g., "xnwv-v1z6-dvnr")

**Example:**
```python
result = await xano_get_instance_details("xnwv-v1z6-dvnr")
# Returns instance details as a dictionary
```

## Database Management

### `xano_list_databases`
List all databases (workspaces) in a specific Xano instance.

**Parameters:**
- `instance_name`: The name of the Xano instance

**Example:**
```python
result = await xano_list_databases("xnwv-v1z6-dvnr")
# Returns: {"databases": [{"id": "123", "name": "MyDatabase", ...}]}
```

### `xano_get_workspace_details`
Get details for a specific Xano workspace.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace

**Example:**
```python
result = await xano_get_workspace_details("xnwv-v1z6-dvnr", "5")
```

## Table Management

### `xano_list_tables`
List all tables in a specific Xano database (workspace).

**Parameters:**
- `instance_name`: The name of the Xano instance
- `database_id`: The ID of the Xano workspace/database

**Example:**
```python
result = await xano_list_tables("xnwv-v1z6-dvnr", "5")
```

### `xano_get_table_details`
Get details for a specific Xano table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table

**Example:**
```python
result = await xano_get_table_details("xnwv-v1z6-dvnr", "5", "10")
```

### `xano_create_table`
Create a new table in a workspace.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `name`: The name of the new table
- `description`: Table description (optional)
- `docs`: Documentation text (optional)
- `auth`: Whether authentication is required (optional)
- `tag`: List of tags for the table (optional)

**Example:**
```python
result = await xano_create_table("xnwv-v1z6-dvnr", 5, "Users", 
                                description="Stores user information")
```

### `xano_update_table`
Update an existing table in a workspace.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table to update
- `name`: The new name of the table (optional)
- `description`: New table description (optional)
- `docs`: New documentation text (optional)
- `auth`: New authentication setting (optional)
- `tag`: New list of tags for the table (optional)

**Example:**
```python
result = await xano_update_table("xnwv-v1z6-dvnr", 5, 10, name="NewTableName")
```

### `xano_delete_table`
Delete a table from a workspace.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table to delete

**Example:**
```python
result = await xano_delete_table("xnwv-v1z6-dvnr", 5, 10)
```

## Schema Management

### `xano_get_table_schema`
Get schema for a specific Xano table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table

**Example:**
```python
result = await xano_get_table_schema("xnwv-v1z6-dvnr", 5, 10)
```

### `xano_add_field_to_schema`
Add a new field to a table schema.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `field_name`: The name of the new field
- `field_type`: The type of the field (e.g., "text", "int", "decimal", "boolean", "date")
- Additional optional parameters for field configuration

**Example:**
```python
# Add a simple text field
result = await xano_add_field_to_schema(
    "xnwv-v1z6-dvnr", 5, 10, 
    field_name="email", 
    field_type="text"
)
```

### `xano_rename_schema_field`
Rename a field in a table schema.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `old_name`: The current name of the field
- `new_name`: The new name for the field

**Example:**
```python
result = await xano_rename_schema_field(
    "xnwv-v1z6-dvnr", 5, 10, 
    old_name="user_email", 
    new_name="email_address"
)
```

### `xano_delete_field`
Delete a field from a table schema.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `field_name`: The name of the field to delete

**Example:**
```python
result = await xano_delete_field(
    "xnwv-v1z6-dvnr", 5, 10, 
    field_name="obsolete_field"
)
```

## Index Management

### `xano_list_indexes`
List all indexes for a table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table

**Example:**
```python
result = await xano_list_indexes("xnwv-v1z6-dvnr", 5, 10)
```

### `xano_create_btree_index`
Create a btree index on a table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `fields`: List of fields and operations for the index

**Example:**
```python
result = await xano_create_btree_index(
    "xnwv-v1z6-dvnr", 5, 10,
    fields=[{"name": "email", "op": "asc"}]
)
```

### `xano_create_unique_index`
Create a unique index on a table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `fields`: List of fields and operations for the index

**Example:**
```python
result = await xano_create_unique_index(
    "xnwv-v1z6-dvnr", 5, 10,
    fields=[{"name": "email", "op": "asc"}]
)
```

### `xano_create_search_index`
Create a search index on a table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `name`: Name for the search index
- `lang`: Language for the search index (e.g., "english", "spanish", etc.)
- `fields`: List of fields and priorities

**Example:**
```python
result = await xano_create_search_index(
    "xnwv-v1z6-dvnr", 5, 10,
    name="content_search",
    lang="english",
    fields=[
        {"name": "title", "priority": 1},
        {"name": "description", "priority": 0.5}
    ]
)
```

### `xano_delete_index`
Delete an index from a table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `index_id`: The ID of the index to delete

**Example:**
```python
result = await xano_delete_index("xnwv-v1z6-dvnr", 5, 10, 15)
```

## Record Management

### `xano_browse_table_content`
Browse content for a specific Xano table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `page`: Page number (default: 1)
- `per_page`: Number of records per page (default: 50)

**Example:**
```python
result = await xano_browse_table_content("xnwv-v1z6-dvnr", 5, 10, page=2)
```

### `xano_search_table_content`
Search table content using complex filtering.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `search_conditions`: List of search conditions
- `sort`: Dictionary with field names as keys and "asc" or "desc" as values
- `page`: Page number (default: 1)
- `per_page`: Number of records per page (default: 50)

**Example:**
```python
result = await xano_search_table_content(
    "xnwv-v1z6-dvnr", 5, 10,
    search_conditions=[
        {"field": "status", "operator": "equals", "value": "active"}
    ],
    sort={"created_at": "desc"}
)
```

### `xano_get_table_record`
Get a specific record from a table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `record_id`: The ID of the record to retrieve

**Example:**
```python
result = await xano_get_table_record("xnwv-v1z6-dvnr", 5, 10, 100)
```

### `xano_create_table_record`
Create a new record in a table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `record_data`: The data for the new record

**Example:**
```python
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

### `xano_update_table_record`
Update an existing record in a table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `record_id`: The ID of the record to update
- `record_data`: The updated data for the record

**Example:**
```python
result = await xano_update_table_record(
    "xnwv-v1z6-dvnr", 5, 10, 100,
    record_data={
        "status": "inactive",
        "last_updated": "2023-08-15T14:30:00Z"
    }
)
```

### `xano_delete_table_record`
Delete a specific record from a table.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `record_id`: The ID of the record to delete

**Example:**
```python
result = await xano_delete_table_record("xnwv-v1z6-dvnr", 5, 10, 100)
```

### `xano_bulk_create_records`
Create multiple records in a table in a single operation.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `records`: List of record data to insert
- `allow_id_field`: Whether to allow setting the ID field

**Example:**
```python
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

### `xano_bulk_update_records`
Update multiple records in a table in a single operation.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `updates`: List of update operations, each containing row_id and updates

**Example:**
```python
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

### `xano_bulk_delete_records`
Delete multiple records from a table in a single operation.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `record_ids`: List of record IDs to delete

**Example:**
```python
result = await xano_bulk_delete_records(
    "xnwv-v1z6-dvnr", 5, 10,
    record_ids=[100, 101, 102]
)
```

### `xano_truncate_table`
Truncate a table, optionally resetting the primary key.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `table_id`: The ID of the table
- `reset`: Whether to reset the primary key counter

**Example:**
```python
# Truncate a table and reset the ID counter to 1
result = await xano_truncate_table("xnwv-v1z6-dvnr", "5", "10", reset=True)
```

## File Management

### `xano_list_files`
List files within a workspace.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- Additional parameters for filtering and sorting

**Example:**
```python
result = await xano_list_files("xnwv-v1z6-dvnr", 5)
```

### `xano_get_file_details`
Get details for a specific file.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `file_id`: The ID of the file

**Example:**
```python
result = await xano_get_file_details("xnwv-v1z6-dvnr", 5, 10)
```

### `xano_delete_file`
Delete a file from a workspace.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `file_id`: The ID of the file to delete

**Example:**
```python
result = await xano_delete_file("xnwv-v1z6-dvnr", 5, 10)
```

### `xano_bulk_delete_files`
Delete multiple files from a workspace in a single operation.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `file_ids`: List of file IDs to delete

**Example:**
```python
result = await xano_bulk_delete_files(
    "xnwv-v1z6-dvnr", 5, 
    file_ids=[10, 11, 12]
)
```

## API Management

### `xano_browse_api_groups`
Browse API groups in a workspace.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- Additional parameters for filtering and sorting

**Example:**
```python
result = await xano_browse_api_groups("xnwv-v1z6-dvnr", 5)
```

### `xano_get_api_group`
Get details for a specific API group.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `apigroup_id`: The ID of the API group

**Example:**
```python
result = await xano_get_api_group("xnwv-v1z6-dvnr", 5, 10)
```

### `xano_create_api_group`
Create a new API group in a workspace.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `name`: The name of the new API group
- Additional optional parameters

**Example:**
```python
result = await xano_create_api_group(
    "xnwv-v1z6-dvnr", 5, 
    name="Authentication APIs"
)
```

### `xano_browse_apis_in_group`
Browse APIs within a specific API group.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `apigroup_id`: The ID of the API group
- Additional parameters for filtering and sorting

**Example:**
```python
result = await xano_browse_apis_in_group("xnwv-v1z6-dvnr", 5, 10)
```

### `xano_get_api`
Get details for a specific API.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `apigroup_id`: The ID of the API group
- `api_id`: The ID of the API

**Example:**
```python
result = await xano_get_api("xnwv-v1z6-dvnr", 5, 10, 15)
```

### `xano_create_api`
Create a new API within an API group.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `apigroup_id`: The ID of the API group
- `name`: The name of the new API
- `verb`: HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD)
- Additional optional parameters

**Example:**
```python
result = await xano_create_api(
    "xnwv-v1z6-dvnr", 5, 10,
    name="Get User Profile",
    verb="GET"
)
```

## Export Operations

### `xano_export_workspace`
Export a workspace to a file.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace to export
- `branch`: Branch to export (defaults to live branch if not specified)
- `password`: Password to encrypt the export (optional)

**Example:**
```python
result = await xano_export_workspace("xnwv-v1z6-dvnr", 5)
```

### `xano_export_workspace_schema`
Export only the schema of a workspace to a file.

**Parameters:**
- `instance_name`: The name of the Xano instance
- `workspace_id`: The ID of the workspace
- `branch`: Branch to export (defaults to live branch if not specified)
- `password`: Password to encrypt the export (optional)

**Example:**
```python
result = await xano_export_workspace_schema("xnwv-v1z6-dvnr", 5)
```