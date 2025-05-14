@echo off
echo Installing Xano MCP Server for Claude Desktop...

rem Install dependencies
pip install -r requirements.txt

rem Determine Claude config path
set CONFIG_DIR=%APPDATA%\Claude
set CONFIG_FILE=%CONFIG_DIR%\claude_desktop_config.json

rem Create config directory if it doesn't exist
if not exist "%CONFIG_DIR%" (
    echo Creating Claude configuration directory...
    mkdir "%CONFIG_DIR%"
)

rem Get absolute path to script
set SCRIPT_PATH=%~dp0xano_mcp_sdk.py
rem Replace backslashes with forward slashes in path
set SCRIPT_PATH=%SCRIPT_PATH:\=/%

if exist "%CONFIG_FILE%" (
    echo Found existing Claude configuration at %CONFIG_FILE%
    echo Backing up original configuration to %CONFIG_FILE%.bak
    copy "%CONFIG_FILE%" "%CONFIG_FILE%.bak"
    
    findstr "mcpServers" "%CONFIG_FILE%" >nul
    if not errorlevel 1 (
        echo The configuration already has MCP servers defined.
        echo Please manually add the Xano MCP server to your configuration.
        echo You can use the claude_desktop_config.json in this folder as a reference.
    ) else (
        echo Updating Claude configuration...
        echo {> "%CONFIG_FILE%"
        echo   "mcpServers": {>> "%CONFIG_FILE%"
        echo     "xano": {>> "%CONFIG_FILE%"
        echo       "command": "python",>> "%CONFIG_FILE%"
        echo       "args": [>> "%CONFIG_FILE%"
        echo         "%SCRIPT_PATH%">> "%CONFIG_FILE%"
        echo       ],>> "%CONFIG_FILE%"
        echo       "env": {>> "%CONFIG_FILE%"
        echo         "XANO_API_TOKEN": "your-xano-api-token">> "%CONFIG_FILE%"
        echo       }>> "%CONFIG_FILE%"
        echo     }>> "%CONFIG_FILE%"
        echo   }>> "%CONFIG_FILE%"
        echo }>> "%CONFIG_FILE%"
        echo Claude configuration updated.
        echo Please edit %CONFIG_FILE% to add your Xano API token.
    )
) else (
    echo Creating Claude configuration file...
    echo {> "%CONFIG_FILE%"
    echo   "mcpServers": {>> "%CONFIG_FILE%"
    echo     "xano": {>> "%CONFIG_FILE%"
    echo       "command": "python",>> "%CONFIG_FILE%"
    echo       "args": [>> "%CONFIG_FILE%"
    echo         "%SCRIPT_PATH%">> "%CONFIG_FILE%"
    echo       ],>> "%CONFIG_FILE%"
    echo       "env": {>> "%CONFIG_FILE%"
    echo         "XANO_API_TOKEN": "your-xano-api-token">> "%CONFIG_FILE%"
    echo       }>> "%CONFIG_FILE%"
    echo     }>> "%CONFIG_FILE%"
    echo   }>> "%CONFIG_FILE%"
    echo }>> "%CONFIG_FILE%"
    echo Claude configuration created.
    echo Please edit %CONFIG_FILE% to add your Xano API token.
)

echo Installation complete!
echo Please restart Claude for Desktop to load the Xano MCP server.
pause
