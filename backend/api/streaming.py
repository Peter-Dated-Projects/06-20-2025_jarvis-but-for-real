from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit

from flask import current_app as app
from backend import (
    SocketIOInstance,
    ClientHandlerObject,
    SoftwareHandlerObject,
)

import os


# --------------------------------------------------------------------------- #
# blueprint + constants
# --------------------------------------------------------------------------- #

streaming_bp = Blueprint("streaming_bp", __name__)

socket_io_instance = SocketIOInstance.get_instance()

DEFAULT_MODEL = "assets/models/ggml-small.en.bin"


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #


@socket_io_instance.on("connect", namespace="/streaming")
def handle_connect():
    # just print out the connection
    print("[CONNECT] Client connected for audio streaming:", request.sid)

    # emit an acknowledgment to the client
    emit(
        "confirm_connect",
        {"message": "Connected to audio streaming server", "sid": request.sid},
        namespace="/streaming",
    )


@socket_io_instance.on("setup_connect", namespace="/streaming")
def handle_setup_connect(data):
    """
    Handle the initial connection for audio streaming.

    This function initializes the audio stream for a new client connection.
    Emits a response to the client indicating successful connection.

    @param request: The Flask request object containing the session ID.
    {
        "sid": str,  # The session ID of the client
        "sender": str ["client", "server", "software"]
    }

    @response:
    - "error": If the streaming key is invalid or initialization fails
    - "response": Confirmation that the client is connected to the server


    """
    print("[SETUP] Audio Streaming:", request.sid)

    # create data using the object-oriented approach
    sender = data.get("sender", None)
    if not sender or sender not in ["client", "software"]:
        emit(
            "error",
            {"message": "Invalid sender type. Must be 'client' or 'software'."},
            namespace="/streaming",
        )
        return

    # check sender
    if sender == "software":
        SoftwareHandlerObject.get_instance().streaming_id = request.sid
        print("Software connected for audio streaming.")
    elif sender == "client":
        ClientHandlerObject.get_instance().streaming_id = request.sid
        print("Client connected for audio streaming.")

    # emit a response to the client
    emit(
        "confirm_connect",
        {"message": "Connected to audio streaming server", "sid": request.sid},
        namespace="/streaming",
    )

    # wait a 5 seconds
    import time

    time.sleep(5)

    # end the connection
    print("[END CONNECTION] Audio Streaming:", request.sid)
    emit(
        "disconnect",
        {"message": "Connection ended", "sid": request.sid},
        namespace="/streaming",
    )


@socket_io_instance.on("disconnect", namespace="/streaming")
def handle_disconnect():
    print("Client disconnected", request.sid)


# real time operations
@socket_io_instance.on("real_time_stt_enable")
def handle_real_time_stt_enable(data):
    """
    Enable real-time speech-to-text (STT) streaming.

    This function is triggered when a client requests to enable real-time STT.
    It initializes the STT process and sends a confirmation response back to the client.

    @param data: The data sent by the client, expected to contain:
    {
        "sid": str,
        "sender": str ["client"/"server"]
    }

    @response:
    - "error": If the streaming key is invalid or initialization fails
    - "response": Confirmation that real-time STT is enabled
    """

    print("[REAL TIME STT ENABLE] Audio Streaming:", request.sid)

    # create data using the object-oriented approach
    ClientHandlerObject.get_instance()

    # send a response to EVERYONE
    emit(
        "real_time_stt_enable",
        {"message": "Real-time STT enabled", "sid": request.sid},
        namespace="/streaming",
        broadcast=True,
    )


@socket_io_instance.on("real_time_stt_disable")
def handle_real_time_stt_disable(data):
    """
    Disable real-time speech-to-text (STT) streaming.

    This function is triggered when a client requests to disable real-time STT.
    It stops the STT process and sends a confirmation response back to the client.

    @param data: The data sent by the client, expected to contain:
    {
        "sid": str,
        "sender": str ["client"/"server"]
    }

    @response:
    - "error": If the streaming key is invalid or initialization fails
    - "response": Confirmation that real-time STT is disabled
    """

    print("[REAL TIME STT DISABLE] Audio Streaming:", request.sid)

    # create data using the object-oriented approach
    ClientHandlerObject.get_instance()

    # send a response to EVERYONE
    emit(
        "real_time_stt_disable",
        {"message": "Real-time STT disabled", "sid": request.sid},
        namespace="/streaming",
        broadcast=True,
    )
