#!/bin/bash

# Xano MCP Local Installation Script

echo "Installing Xano MCP Server for Claude Desktop..."

# Install dependencies
pip install -r requirements.txt

# Make the script executable
chmod +x xano_mcp_sdk.py

# Determine Claude config path
CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

if [ -f "$CONFIG_FILE" ]; then
    echo "Found existing Claude configuration at $CONFIG_FILE"
    echo "Backing up original configuration to ${CONFIG_FILE}.bak"
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
    
    # Check if file contains mcpServers
    if grep -q "mcpServers" "$CONFIG_FILE"; then
        echo "The configuration already has MCP servers defined."
        echo "Please manually add the Xano MCP server to your configuration."
        echo "You can use the claude_desktop_config.json in this folder as a reference."
    else
        echo "Updating Claude configuration..."
        SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/xano_mcp_sdk.py"
        cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "xano": {
      "command": "python",
      "args": [
        "$SCRIPT_PATH"
      ],
      "env": {
        "XANO_API_TOKEN": "your-xano-api-token"
      }
    }
  }
}
EOF
        echo "Claude configuration updated."
        echo "Please edit $CONFIG_FILE to add your Xano API token."
    fi
else
    echo "Creating Claude configuration directory..."
    mkdir -p "$CONFIG_DIR"
    
    echo "Creating Claude configuration file..."
    SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/xano_mcp_sdk.py"
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "xano": {
      "command": "python",
      "args": [
        "$SCRIPT_PATH"
      ],
      "env": {
        "XANO_API_TOKEN": "your-xano-api-token"
      }
    }
  }
}
EOF
    echo "Claude configuration created."
    echo "Please edit $CONFIG_FILE to add your Xano API token."
fi

echo "Installation complete!"
echo "Please restart Claude for Desktop to load the Xano MCP server."
