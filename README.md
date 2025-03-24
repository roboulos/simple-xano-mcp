# Xano MCP Server

This is a simplified Model Context Protocol (MCP) server for Xano database integration. It allows Claude to interact with Xano databases through the Xano Metadata API.

## Features

This MCP server provides core tools for:

- Listing Xano instances
- Getting instance details
- Listing databases in an instance
- Listing tables in a database
- Getting table details

## Local Usage

### Prerequisites

- Python 3.8 or higher
- A valid Xano Metadata API token

### Installation

```bash
# Install dependencies
pip install httpx "mcp[cli]"
```

### Running the Server

```bash
# Run with your Xano token
python xano_mcp_sdk.py --token "YOUR_XANO_API_TOKEN"
```

## Smithery.ai Deployment

This repository is configured for deployment on Smithery.ai.

### Deployment Steps

1. Add your server on Smithery.ai
2. Set your Xano API token as the configuration parameter
3. Deploy your server

## API Endpoint Structure

The implementation uses the Xano API with this structure:

- Authentication: `/auth/me` 
- Browse instances: `/instance` 
- List databases: `/instance/{name}/workspace` 
- List tables: `/instance/{name}/database/{name}/table`

## Implementation

The MCP server uses the FastMCP SDK for Python, which ensures protocol compliance and proper handling of MCP requests and responses.
