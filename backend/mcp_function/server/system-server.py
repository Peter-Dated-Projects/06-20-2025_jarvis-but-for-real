import subprocess
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("system")

# Brightness
@mcp.tool()
async def brightness_up() -> str:
    subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 144'], check=True)
    subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 144'], check=True)
    subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 144'], check=True)
    return "Increased screen brightness."

# Brightness
@mcp.tool()
async def brightness_down() -> str:
    subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 145'], check=True)
    subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 145'], check=True)
    subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 145'], check=True)
    return "Decreased screen brightness."

# Volume
@mcp.tool()
async def volume_up() -> str:
    subprocess.run([
        'osascript',
        '-e', 'set cur to output volume of (get volume settings)',
        '-e', 'set volume output volume (cur + 25)'
    ], check=True)
    return "Increased system volume."

# Volume
@mcp.tool()
async def volume_down() -> str:
    subprocess.run([
        'osascript',
        '-e', 'set cur to output volume of (get volume settings)',
        '-e', 'set volume output volume (cur - 25)'
    ], check=True)
    return "Decreased system volume."

# Screenshot
@mcp.tool()
async def screenshot_clipboard() -> str:
    subprocess.run(['screencapture', '-c'], check=True)
    return "Screenshot taken and copied to clipboard."

# Open Application
@mcp.tool()
async def open_application(app_name: str) -> str:
    try:
        subprocess.run(['open', '-a', app_name], check=True)
        return f"Opened application: {app_name}"
    except subprocess.CalledProcessError:
        return f"Failed to open application: {app_name}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
