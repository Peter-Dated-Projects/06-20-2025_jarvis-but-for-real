# MCP (Model Context Protocol) Integration

This document describes the integration of MCP (Model Context Protocol) functionality into the Flask application.

## Overview

The MCP integration allows the Flask application to:
- Connect to various MCP servers (Google Workspace, Spotify, Terminal)
- Process natural language queries using Gemini AI
- Execute tools and functions through MCP servers
- Maintain conversation history
- Generate audio responses using text-to-speech

## Architecture

```
Flask App (main.py)
    ↓
MCPClient (client.py)
    ↓
MCP Servers:
- Google Workspace (Docker)
- Spotify (Python)
- Terminal (Python)
    ↓
Gemini AI (for query processing)
```

## Setup Instructions

### 1. Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Google Workspace MCP
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Flask App
BACKEND_HOST=localhost
BACKEND_PORT=5001
DEBUG=True
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Docker Setup (for Google Workspace MCP)

The Google Workspace MCP server runs in Docker. Make sure you have:
- Docker installed and running
- Google Workspace MCP image built or pulled

### 4. MCP Server Setup

Ensure the MCP servers are available:
- `backend/mcp/server/spotify-server.py`
- `backend/mcp/server/terminal-server.py`
- Google Workspace MCP Docker container

## API Endpoints

### POST /query

Process a natural language query using MCP tools.

**Request:**
```json
{
    "query": "What's the weather like today?"
}
```

**Response:**
```json
{
    "response": "Based on the current weather data..."
}
```

### POST /cleanup

Clean up MCP client connections.

**Response:**
```json
{
    "status": "success",
    "message": "MCP client cleaned up successfully"
}
```

## Usage Examples

### 1. Basic Query

```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What time is it?"}'
```

### 2. Using Python Requests

```python
import requests

response = requests.post(
    "http://localhost:5001/query",
    json={"query": "Can you help me create a new document?"}
)

print(response.json()["response"])
```

### 3. Testing Integration

Run the test script to verify everything is working:

```bash
cd backend
python test_mcp_integration.py
```

## Features

### Conversation History
- Maintains conversation context across multiple queries
- Configurable history length (default: 4 interactions)
- Includes previous Q&A pairs in prompts

### Multi-Step Reasoning
- Supports up to 3 iterations of tool calls
- Handles complex queries requiring multiple tools
- Provides detailed error messages and tracebacks

### Tool Integration
- **Google Workspace**: Document creation, email, calendar
- **Spotify**: Music playback, playlist management
- **Terminal**: System commands and file operations

### Audio Generation
- Text-to-speech using Kokoro pipeline
- Supports multiple voices
- Saves audio segments as WAV files

## Error Handling

The integration includes comprehensive error handling:

1. **Missing Dependencies**: Graceful fallback if MCP client is unavailable
2. **Connection Errors**: Detailed error messages for server connection issues
3. **Tool Execution Errors**: Error messages and tracebacks for failed tool calls
4. **Timeout Handling**: Configurable timeouts for long-running operations

## Configuration

### MCP Client Configuration

You can modify the MCP client behavior in `main.py`:

```python
# Change history length
app.mcp_client = MCPClient(history_length=10)

# Custom server configurations
server_configs = {
    "custom_server": {
        "command": "python3",
        "args": ["path/to/custom/server.py"]
    }
}
```

### Flask Configuration

Environment variables for Flask app:

- `BACKEND_HOST`: Server host (default: localhost)
- `BACKEND_PORT`: Server port (default: 5001)
- `DEBUG`: Debug mode (default: True)

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path includes MCP client directory

2. **Connection Errors**
   - Verify MCP servers are running
   - Check Docker is running (for Google Workspace MCP)
   - Ensure environment variables are set correctly

3. **Timeout Errors**
   - First-time setup may take longer due to model downloads
   - Increase timeout values for slow operations

4. **Authentication Errors**
   - Verify API keys and credentials are correct
   - Check Google Workspace OAuth setup

### Debug Mode

Enable debug mode for detailed logging:

```bash
export DEBUG=True
python main.py
```

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use `.env` files for sensitive data
3. **CORS**: Configure CORS settings for production use
4. **Authentication**: Implement proper authentication for production

## Performance

- **Caching**: MCP client maintains connections for better performance
- **Async Operations**: Non-blocking async operations for better responsiveness
- **Resource Management**: Proper cleanup of connections and event loops

## Future Enhancements

1. **Additional MCP Servers**: Support for more MCP servers
2. **WebSocket Integration**: Real-time communication
3. **Streaming Responses**: Stream responses for better UX
4. **Advanced Audio**: More audio formats and voice options
5. **Caching Layer**: Redis-based caching for responses 