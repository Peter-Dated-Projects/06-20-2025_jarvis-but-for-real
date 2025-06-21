from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit

from flask import current_app as app
from backend import (
    SocketIOInstance,
    AudioBuffersInstance,
    CACHE_STREAMING_KEY,
    CACHE_AUDIO_DATA,
    CACHE_FILE_PATH,
    CACHE_FILE_URL,
)

import os
import ffmpeg

from typing import Optional, Union, List, Dict, Any


# --------------------------------------------------------------------------- #
# blueprint
# --------------------------------------------------------------------------- #

streaming_bp = Blueprint("streaming_bp", __name__)

socket_io_instance = SocketIOInstance.get_instance()


# --------------------------------------------------------------------------- #
# verification functions
# --------------------------------------------------------------------------- #


def is_valid_streaming_key(key: str) -> bool:
    """Check if the streaming key is valid."""
    # Check if the key exists in the _AUDIO_BUFFERS
    return key in AudioBuffersInstance.get_instance()


def is_audio_buffer_empty(key: str) -> bool:
    """Check if the audio buffer is empty."""
    # Check if the key exists and if its buffer is empty
    return is_valid_streaming_key(key) and len(AudioBuffersInstance()[key]) == 0


def process_audio(key: str) -> bool:
    """Process the audio buffer."""
    # Check if the key exists and process the audio
    if not is_valid_streaming_key(key):
        return False

    _audio_instance = AudioBuffersInstance.get_instance()
    audio_chunks = _audio_instance[key][CACHE_AUDIO_DATA]

    # Combine the chunks into a single blob
    audio_blob = b"".join(audio_chunks)

    print(f"This is the streaming key: {_audio_instance[key][CACHE_STREAMING_KEY]}")
    print(_audio_instance[key][CACHE_FILE_PATH])
    print(f"Audio buffer length: {len(audio_blob)}")

    # check if folder exists
    if not os.path.exists(app.config["AUDIO_CACHE_DIR"]):
        os.makedirs(app.config["AUDIO_CACHE_DIR"])
        print("Created audio cache directory")

    # save the audio file as a webm file
    try:
        _temp_file = os.path.join(
            app.config["AUDIO_CACHE_DIR"], f"recording_{key}.webm"
        )

        with open(_temp_file, "wb") as f:
            f.write(audio_blob)
        print("Saved audio blob to raw temporary file at:", _temp_file)

        _final_file = _audio_instance[key][CACHE_FILE_PATH]

        # ffmpeg to save file as proper format

        ffmpeg.input(_temp_file).output(
            _final_file, ar=16000, ac=1, acodec="pcm_s16le"
        ).run(quiet=False, overwrite_output=True)

        print("Saved audio data to wav file: ", _final_file)

        # create file url
        base_url = app.config.get(
            "AUDIO_BASE_URL",
            f"http://{os.getenv('BACKEND_HOST')}:{os.getenv('BACKEND_PORT')}/static/audio",
        )
        file_url = f"{base_url}/{os.path.basename(_final_file)}"
        _audio_instance[key][CACHE_FILE_URL] = file_url

        # delete temp file
        os.remove(_temp_file)
        print("Deleted temporary file: ", _temp_file)
    except FileNotFoundError:
        print("File not found error")
        return False
    except Exception as e:
        print(f"Error processing audio: {e}")
        return False

    print(f"Audio processed and saved to {_final_file}")

    return True


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #


@socket_io_instance.on("connect", namespace="/streaming")
def handle_connect():
    print("Client connected", request.sid)
    sid = request.sid

    _audio_instance = AudioBuffersInstance.get_instance()

    _audio_instance[sid] = {
        CACHE_STREAMING_KEY: sid,
        CACHE_FILE_PATH: os.path.join(app.config["AUDIO_CACHE_DIR"], f"{sid}.wav"),
        CACHE_AUDIO_DATA: [],
        CACHE_FILE_URL: None,
    }

    # check if valid streaming key
    if not is_valid_streaming_key(sid):
        emit("error", {"message": "Invalid streaming key"})
        return

    emit("response", {"message": "Connected to server"})


@socket_io_instance.on("stop_recording", namespace="/streaming")
def handle_stop_recording():
    sid = request.sid

    # check if valid streaming key
    if not is_valid_streaming_key(sid):
        emit("error", {"message": "Invalid streaming key"})
        return

    _audio_instance = AudioBuffersInstance.get_instance()

    # return the audio file path
    print("Emitting file path: ", _audio_instance[sid][CACHE_FILE_PATH])
    file_path = _audio_instance[sid][CACHE_FILE_PATH]

    # Construct a public URL for the audio file.
    base_url = app.config.get(
        "AUDIO_BASE_URL",
        f"http://{os.getenv('BACKEND_HOST')}:{os.getenv('BACKEND_PORT')}/static/audio",
    )
    file_url = f"{base_url}/{os.path.basename(file_path)}"
    _audio_instance[sid][CACHE_FILE_URL] = file_url

    # process the file first
    if not process_audio(sid):
        emit("error", {"message": "Failed to process audio"})
        return
    print(f"Saved recording for client {sid}")

    # emit the file path to the client
    emit(
        "result_file_path",
        {
            "streaming_id": sid,
            "message": "Disconnected from server",
            "file_url": _audio_instance[sid][CACHE_FILE_URL],
        },
    )


@socket_io_instance.on("disconnect", namespace="/streaming")
def handle_disconnect():
    print("Client disconnected", request.sid)
    sid = request.sid

    # check if valid streaming key
    if not is_valid_streaming_key(sid):
        emit("error", {"message": "Invalid streaming key"})
        return


@socket_io_instance.on("audio_chunk", namespace="/streaming")
def handle_audio_chunk(data):
    """Handle incoming audio chunk."""
    sid = request.sid
    # check if valid streaming id
    if not sid:
        emit("error", {"message": "Invalid streaming key"})

    # check if valid streaming key
    if not is_valid_streaming_key(sid):
        emit("error", {"message": "Invalid streaming key"}, namespace="/streaming")
        return

    _chunk = data["chunk"]
    print("Received chunk: length = ", len(_chunk))

    # Append the received audio data to the buffer
    _audio_instance = AudioBuffersInstance.get_instance()
    _audio_instance[sid][CACHE_AUDIO_DATA].append(_chunk)

    # Optionally, send back a response
    emit("response", {"message": "received chunk"}, namespace="/streaming")


@streaming_bp.route("/force_stop", methods=["POST"])
def streaming_finalize_audio():
    """Force stop audio streaming."""
    _sid = request.session_id
    # check if valid streaming key
    if not is_valid_streaming_key(_sid):
        return jsonify({"error": "Invalid streaming key"}), 400

    # check if audio buffer is empty
    if is_audio_buffer_empty(_sid):
        return jsonify({"error": "Audio buffer is empty"}), 400

    # process + clean up buffered audio data
    if not process_audio(_sid):
        return jsonify({"error": "Failed to process audio"}), 500

    return jsonify({"message": "Audio processing complete"}), 200
