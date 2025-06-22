import os
import subprocess
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

def start_docker_container():
    """Starts the Google Workspace MCP Docker container."""
    print("🚀 Starting Google Workspace MCP server in Docker...")
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not google_client_id or not google_client_secret:
        raise ValueError(
            "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET not found. "
            "Please add them to your .env file."
        )

    docker_args = [
        "docker", "run", "--rm", "-i",
        "-p", "8080:8080",
        "-v", f"{os.path.expanduser('~')}/.mcp/google-workspace-mcp:/app/config",
        "-v", f"{os.path.expanduser('~')}/Documents/workspace-mcp-files:/app/workspace",
        "-e", f"GOOGLE_CLIENT_ID={google_client_id}",
        "-e", f"GOOGLE_CLIENT_SECRET={google_client_secret}",
        "-e", "LOG_MODE=strict",
        "google-workspace-mcp:local"
    ]
    
    # We run this in the background. Note that this is a simple approach.
    # For a production scenario, you'd want more robust process management.
    subprocess.Popen(docker_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("✅ Docker container started.")

# Create an MCP server instance
mcp = FastMCP("google_tools_proxy")

# You can add tools here that might interact with the Docker container
# For example, a tool to check its logs or status.
# For now, we will leave it empty as requested.

if __name__ == "__main__":
    # Start the Docker container first
    start_docker_container()
    
    # Then run the MCP server
    mcp.run(transport='stdio')
