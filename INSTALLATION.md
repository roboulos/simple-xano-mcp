# Xano MCP Python SDK - Detailed Installation Guide

This guide provides step-by-step instructions for installing and setting up the Xano MCP Python SDK for various use cases and platforms.

## Prerequisites

Before you begin, ensure you have:

- Python 3.7 or later installed
- pip (Python package manager)
- A Xano account with API access
- Your Xano API token

## Installation Options

Choose one of the following installation methods:

### Method 1: Automated Installation (Recommended)

#### For macOS/Linux:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/xano-mcp-python.git
   cd xano-mcp-python
   ```

2. Run the installation script:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. When prompted, enter your Xano API token.

#### For Windows:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/xano-mcp-python.git
   cd xano-mcp-python
   ```

2. Run the installation script:
   ```bash
   install.bat
   ```

3. When prompted, enter your Xano API token.

### Method 2: Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/xano-mcp-python.git
   cd xano-mcp-python
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make the SDK executable (Linux/macOS only):
   ```bash
   chmod +x xano_mcp_sdk.py
   ```

4. Configure for Claude Desktop (if using):

   Edit your Claude configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

   Add the following configuration:
   ```json
   {
     "mcpServers": {
       "xano": {
         "command": "python",
         "args": [
           "/full/path/to/xano-mcp-python/xano_mcp_sdk.py"
         ],
         "env": {
           "XANO_API_TOKEN": "your-xano-api-token"
         }
       }
     }
   }
   ```

   Replace `/full/path/to/xano-mcp-python/xano_mcp_sdk.py` with the actual full path to the SDK file.

## Integration Methods

### Claude Desktop Integration

After installation, the SDK will be available in Claude Desktop. Look for the hammer icon in the input area, which indicates that tools are available. You can ask Claude about your Xano instances, tables, and perform operations.

### Command-Line Usage

You can also run the SDK directly from the command line:

```bash
# With environment variable
XANO_API_TOKEN=your-token python xano_mcp_sdk.py

# With command-line argument
python xano_mcp_sdk.py --token your-token
```

### API Integration

For advanced use cases, you can integrate the SDK into your own Python applications:

```python
import asyncio
from xano_mcp_sdk import XanoMcpSDK

async def main():
    xano = XanoMcpSDK(api_token="your-token")
    instances = await xano.list_instances()
    print(instances)

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration Options

### Environment Variables

The SDK supports the following environment variables:

- `XANO_API_TOKEN` (required): Your Xano API token
- `XANO_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `XANO_DEFAULT_INSTANCE`: Default instance name to use
- `XANO_CONFIG_PATH`: Path to a config file (optional)

### Command-Line Arguments

The SDK supports the following command-line arguments:

- `--token <token>`: Xano API token
- `--log-level <level>`: Set logging level
- `--instance <name>`: Default instance name
- `--config <path>`: Path to config file
- `--console-logging`: Log to console instead of file

## Testing Your Installation

To verify that your installation works correctly:

```bash
# Run the test script
python test.py
```

This will perform a basic connectivity test with your Xano account and verify that authentication is working.

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify your Xano API token is correct
   - Check that it has the necessary permissions

2. **Path Issues**:
   - Ensure all file paths in configuration files are absolute
   - On Windows, use double backslashes in paths: `C:\\Users\\...`

3. **Python Environment**:
   - Ensure you have Python 3.7+
   - Try creating a virtual environment if there are package conflicts

4. **Claude Integration**:
   - Restart Claude Desktop after making configuration changes
   - Check Claude Desktop logs for errors

### Checking Logs

To view logs for troubleshooting:

**macOS**:
```bash
tail -n 100 -f ~/Library/Logs/Claude/mcp*.log
```

**Windows**:
```bash
type "%APPDATA%\Claude\logs\mcp*.log"
```

## Upgrading

To upgrade to the latest version:

1. Pull the latest changes:
   ```bash
   cd xano-mcp-python
   git pull
   ```

2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the installation script again (optional):
   ```bash
   # macOS/Linux
   ./install.sh
   
   # Windows
   install.bat
   ```

## Uninstallation

To uninstall:

1. Remove the SDK configuration from Claude Desktop by editing:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Delete the repository folder:
   ```bash
   rm -rf /path/to/xano-mcp-python
   ```