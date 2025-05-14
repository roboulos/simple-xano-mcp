# Xano MCP Python SDK

A Python-based MCP (Model Context Protocol) server for Xano that allows AI assistants like Claude to interact directly with your Xano instance. This is a standalone version optimized for local use with Claude Desktop and other MCP-compatible LLMs.

## 🌟 Features

- **Simple Authentication**: Connect with your Xano API token
- **Comprehensive API**: Query and manipulate Xano instances, databases, tables, and records
- **Local Deployment**: Run as a local MCP server for Claude Desktop or other clients
- **Detailed Logging**: Troubleshoot issues with comprehensive logging
- **Portable**: Works on macOS, Windows, and Linux

## 🚀 Quick Start

1. **Clone this repository**:
   ```bash
   git clone https://github.com/yourusername/xano-mcp-python.git
   cd xano-mcp-python
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Claude Desktop** (if using):
   
   Edit your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

   Add this configuration:
   ```json
   {
     "mcpServers": {
       "xano": {
         "command": "python",
         "args": [
           "/path/to/xano-mcp-python/xano_mcp_sdk.py"
         ],
         "env": {
           "XANO_API_TOKEN": "your-xano-api-token"
         }
       }
     }
   }
   ```

4. **Run the installation script**:
   ```bash
   # On macOS/Linux
   ./install.sh
   
   # On Windows
   install.bat
   ```

5. **Test the installation**:
   ```bash
   ./test.py
   ```

## 💡 Usage Examples

Once installed, you can use it with Claude or any MCP-compatible assistant. Here are some examples:

- **List your Xano instances**:
  > What Xano instances do I have?

- **Check database tables**:
  > Show me all tables in my Xano instance "my-instance"

- **Create a new table**:
  > Create a new table called "products" in my Xano instance "my-instance"

- **Examine table structure**:
  > What's the schema for the "users" table?

- **Query records**:
  > Show me the first 5 records in the "users" table

## 🧰 Available Tools

### Instance Management
- List instances
- Get instance details
- Check instance status

### Database Operations
- List databases/workspaces
- Get workspace details
- Database schema management

### Table Operations
- Create, update, delete tables
- Add, modify, and remove fields
- Index management

### Record Management
- Create, read, update, delete records
- Bulk operations
- Complex queries

### File Operations
- List and manage files
- Upload and download

### API Tools
- API group management
- API endpoint creation and configuration

## 🔧 Advanced Configuration

### Environment Variables

- `XANO_API_TOKEN`: Your Xano API token (required)
- `XANO_LOG_LEVEL`: Set log level (default: INFO)
- `XANO_DEFAULT_INSTANCE`: Default instance to use when not specified

### Command Line Options

```bash
python xano_mcp_sdk.py --token YOUR_TOKEN --log-level DEBUG
```

### Logging

Logs are written to:
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Windows: `%APPDATA%\Claude\logs\mcp*.log`

For direct console output, run:
```bash
python xano_mcp_sdk.py --console-logging
```

## 🚨 Troubleshooting

If you encounter issues:

1. **Check logs** for errors:
   ```bash
   # macOS
   tail -n 100 -f ~/Library/Logs/Claude/mcp*.log
   
   # Windows
   type "%APPDATA%\Claude\logs\mcp*.log"
   ```

2. **Verify API token** is correct and has appropriate permissions

3. **Check network connectivity** to Xano servers

4. **Ensure Python environment** is properly set up

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- Xano for their excellent database platform
- Anthropic for the Model Context Protocol specification
- Contributors and testers who helped refine this SDK