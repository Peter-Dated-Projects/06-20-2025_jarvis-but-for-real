from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit

from flask import current_app as app
from backend import (
    SocketIOInstance,
)

import os


# --------------------------------------------------------------------------- #
# blueprint + constants
# --------------------------------------------------------------------------- #

client_bp = Blueprint("client_bp", __name__)

socket_io_instance = SocketIOInstance.get_instance()

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

    # emit a response to the client
    emit(
        "confirm_connect",
        {"message": "Connected to audio streaming server", "sid": request.sid},
        namespace="/streaming",
    )

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
