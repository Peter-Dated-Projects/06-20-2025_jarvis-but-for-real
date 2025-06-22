import os
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("terminal")
DEFAULT_WORKSPACE = os.path.expanduser("/Users/johnzhang/Desktop/Development/Workspace")

@mcp.tool()
async def run_command(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            cwd=DEFAULT_WORKSPACE
        )
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)
    
@mcp.tool()
async def initiate_repo(repo_name: str) -> str:
    repo_path = os.path.join(DEFAULT_WORKSPACE, repo_name)
    try:
        if os.path.exists(repo_path):
            return f"Repository already exists at {repo_path}."
        else:
            os.makedirs(repo_path, exist_ok=True)
            subprocess.run(['git', 'init'], cwd=repo_path, check=True)
            return f"Initialized new repository at {repo_path}."
    except subprocess.CalledProcessError as e:
        return f"Failed to initialize repository: {e}"

@mcp.tool()    
async def change_workspace(new_workspace: str) -> str:
    global DEFAULT_WORKSPACE
    if os.path.isdir(new_workspace):
        DEFAULT_WORKSPACE = new_workspace
        return f"Changed workspace to: {DEFAULT_WORKSPACE}"
    else:
        return f"Invalid workspace path: {new_workspace}"

if __name__ == "__main__":
    mcp.run(transport='stdio')