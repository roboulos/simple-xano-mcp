FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "mcp[cli]"

# Copy the server code
COPY xano_mcp_sdk.py .

# Make the script executable
RUN chmod +x xano_mcp_sdk.py

# Run the server
CMD ["python", "xano_mcp_sdk.py"]
