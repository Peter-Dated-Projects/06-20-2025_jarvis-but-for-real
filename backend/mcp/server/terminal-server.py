import os
import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("terminal")
DEFAULT_WORKSPACE = os.path.expanduser("~/workspace")

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

if __name__ == "__main__":
    mcp.run(transport='stdio')