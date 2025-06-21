from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit

from flask import current_app as app
from backend import (
    SocketIOInstance,
    AudioBuffersInstance,
    AudioStreamCache,
    WhisperCoreSingleModel,
)

import os
import ffmpeg

from typing import Optional, Union, List, Dict, Any

from source.whispercore_handler import AudioConfig

from pyaudio import paInt16 as pyaudio_paInt16


# --------------------------------------------------------------------------- #
# blueprint + constants
# --------------------------------------------------------------------------- #

streaming_bp = Blueprint("streaming_bp", __name__)


socket_io_instance = SocketIOInstance.get_instance()

DESIRED_AUDIO_CONFIG = AudioConfig(
    sample_rate=16000, channels=1, audio_format=pyaudio_paInt16
)
DEFAULT_MODEL = "assets/models/ggml-base.en.bin"

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


@socket_io_instance.on("connect", namespace="/begin_audio_stream")
def handle_connect():
    """
    Handle the initial connection for audio streaming.

    This function initializes the audio stream for a new client connection.
    Emits a response to the client indicating successful connection.

    @param request: The Flask request object containing the session ID.
    {
        "sid": str,  # The session ID of the client
        "model": Optional[str],  # The model to use for STT, defaults to DEFAULT_MODEL
    }

    @response:
    - "error": If the streaming key is invalid or initialization fails
    - "response": Confirmation that the client is connected to the server


    """
    print("[CONNECT] Audio Streaming:", request.sid)
    sid = request.sid

    # Initialize the audio instance for this session
    _audio_instance = AudioBuffersInstance.get_instance()

    # create data using the object-oriented approach
    result = AudioStreamCache(
        streaming_key=sid,
        file_path=os.path.join(app.config["AUDIO_CACHE_DIR"], f"{sid}.wav"),
        audio_data=[],
        file_url=None,
        model=request.args.get("model", DEFAULT_MODEL),  # Get model from request args
    )

    # add the cache object to the instance
    AudioBuffersInstance.add_cache(sid, result)

    # check if key was actually added
    if not is_valid_streaming_key(sid):
        emit("error", {"message": "Failed to initialize audio stream"})
        return

    # send a response to client
    emit(
        "connect_response",
        {"message": "Connected to server", "model": DEFAULT_MODEL},
        namespace="/begin_audio_stream",
    )


@socket_io_instance.on("real_time_stt_request", namespace="/streaming")
def handle_real_time_stt(data):
    """

    Handle real-time speech-to-text requests.

    @param data:
    {
        "sid": str,  # The session ID of the client

        "real_time": bool,  # Indicates if this is a real-time request
        "audio_data": Union[str, bytes],  # raw audio byte data

        "audio_format": str,  # Format of the audio data (e.g., "wav", "mp3")
        "channels": int,  # Number of audio channels (e.g., 1 for mono, 2 for stereo)
        "sample_rate": int,  # Sample rate of the audio data (e.g., 16000, 44100)
    }

    @response:
    - "error": If the streaming key is invalid or no audio data is provided
    - "response": Confirmation that audio data was received for STT
        - {
            "new_segment": boolean,
            "segment_start": int,
            "segment_end": int,
            "segment_transcript": str,
        }


    """
    sid = request.sid

    # check if valid streaming key
    if not is_valid_streaming_key(sid):
        emit("error", {"message": "Invalid streaming key"})
        return

    # Extract the audio data from the incoming data
    audio_data = data.get("audio_data")
    is_real_time = data.get("real_time")
    audio_format = data.get("audio_format")
    channels = data.get("channels")
    sample_rate = data.get("sample_rate")

    if not audio_format or not channels or not sample_rate:
        emit(
            "error",
            {"message": "Invalid audio format, channels, or sample rate provided"},
        )
        print(
            "[REAL-TIME STT] Invalid audio format, channels, or sample rate provided:",
            data,
        )
        return
    if not audio_data:
        emit("error", {"message": "No audio data provided"})
        return

    _cache = AudioBuffersInstance.get_cache(sid)
    if not _cache:
        emit("error", {"message": "Audio stream not initialized"})
        return

    _dataformat = AudioConfig(
        audio_format=audio_format,
        channels=channels,
        sample_rate=sample_rate,
    )

    # Check for errors in audio data format
    if DESIRED_AUDIO_CONFIG != _dataformat:
        print(
            "[REAL-TIME STT] Audio format does not match desired configuration. Must have the following:",
            DESIRED_AUDIO_CONFIG,
        )
        emit(
            "error",
            {
                "message": "Audio format does not match desired configuration. Must have the following: ",
                "desired": DESIRED_AUDIO_CONFIG,
                "actual": _dataformat,
            },
        )

    # append received audio to a buffer + handle if real time request
    _cache.add_audio_chunk(audio_data)

    if is_real_time:

        # TODO - call the whispercore code
        print("[REAL-TIME STT] Received real-time audio data for processing.")
        if not WhisperCoreSingleModel.get_instance().has_model(_cache._target_model):
            # load the model
            print(
                f"[REAL-TIME STT] Loading model: {_cache._target_model} for real-time processing."
            )
            WhisperCoreSingleModel.get_instance().add_model(_cache._target_model)
        else:
            print(
                f"[REAL-TIME STT] Model {_cache._target_model} already loaded for real-time processing."
            )

        # update the whispercore instance
        _new_segment = _cache._whispercore_handler.get_whisper_core().update_stream()

        # create response + send it
        response = {
            "new_segment": _new_segment,
            "segment_start": 0,
            "segment_end": len(_cache.get_audio_data()) - 1,
            "segment_transcript": "Simulated transcript for real-time audio",
        }
        emit("real_time_stt_response", response, namespace="/streaming")

    # Optionally, send back a response
    emit(
        "real_time_stt_response",
        {"message": "Received audio data for STT"},
        namespace="/streaming",
    )


@socket_io_instance.on("stop_recording", namespace="/streaming")
def handle_stop_recording():
    sid = request.sid

    # check if valid streaming key
    if not is_valid_streaming_key(sid):
        emit("error", {"message": "Invalid streaming key"})
        return

    # return the audio file path
    _cache = AudioBuffersInstance.get_cache(sid)
    if not _cache:
        emit("error", {"message": "Audio stream not initialized"})
        return

    print("Emitting file path: ", _cache.file_path)
    file_path = _cache.file_path

    # Construct a public URL for the audio file.
    base_url = app.config.get(
        "AUDIO_BASE_URL",
        f"http://{os.getenv('BACKEND_HOST')}:{os.getenv('BACKEND_PORT')}/static/audio",
    )
    file_url = f"{base_url}/{os.path.basename(file_path)}"
    _cache._file_url = file_url

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
            "message": "Succeessfully stopped recording + generated audio file.",
            "file_url": _cache._file_url,
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

    # Clean up the audio buffer for this session
    AudioBuffersInstance.clean_cache(sid)
    print(f"Cleaned up audio buffer for session {sid}")


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
