import os
import sys
import shutil
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("spotify")

@mcp.tool()
async def play_song(song_name: str, artist: str) -> str:
    # query song name and artist to get track id
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
    ))
    results = sp.search(q=f"track:{song_name} artist:{artist}", type="track")
    if results["tracks"]["items"]:
        track_id = results["tracks"]["items"][0]["id"]
    else:
        return f"Could not find track '{song_name}' by artist '{artist}'."

    print(f'osascript command: tell application "Spotify" to play track "spotify:track:{track_id}"', file=sys.stderr)
    # run subprocess to open Spotify and play using track id
    subprocess.run(['open', '-a', 'Spotify'])


    try:
        subprocess.run([
            'osascript',
            '-e', f'tell application "Spotify" to play track "spotify:track:{track_id}"'
        ], check=True)

        if not shutil.which("osascript"):
            return "AppleScript is not available on this system."

        return f"Playing '{song_name}' by {artist} in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to play song: {e}"

@mcp.tool()
async def next_track() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to next track'
        ], check=True)
        return "Skipped to next track in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to skip to next track: {e}"

@mcp.tool()
async def previous_track() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to previous track'
        ], check=True)
        return "Went to previous track in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to go to previous track: {e}"

@mcp.tool()
async def playpause() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to playpause'
        ], check=True)
        return "Toggled play/pause in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to toggle play/pause: {e}"

@mcp.tool()
async def pause() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to pause'
        ], check=True)
        return "Paused Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to pause: {e}"

@mcp.tool()
async def play() -> str:
    try:
        subprocess.run([
            'osascript',
            '-e', 'tell application "Spotify" to play'
        ], check=True)
        return "Resumed playback in Spotify app."
    except subprocess.CalledProcessError as e:
        return f"Failed to resume playback: {e}"

if __name__ == "__main__":
    mcp.run(transport='stdio')