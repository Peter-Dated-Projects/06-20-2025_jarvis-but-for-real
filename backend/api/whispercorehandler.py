from flask import Blueprint, request, jsonify

from flask import current_app as app
import requests
from backend import (
    SocketIOInstance,
    ClientHandlerObject,
)

import os


# --------------------------------------------------------------------------- #
# blueprint + constants
# --------------------------------------------------------------------------- #

whisper_core_bp = Blueprint("whisper_core_bp", __name__)
socket_io_instance = SocketIOInstance.get_instance()


PROPAGATE_WHISPER_EVENTS_NAMESPACE = "/propagate_whisper_events"


# --------------------------------------------------------------------------- #
# socket events
# --------------------------------------------------------------------------- #


@socket_io_instance.on("connect", namespace=PROPAGATE_WHISPER_EVENTS_NAMESPACE)
def handle_connect():
    """
    Handle the connection event for the whisper core handler.
    This function is called when a client connects to the whisper core handler.
    """
    print("[CONNECT] Whisper core handler connected:", request.sid)

    # emit an acknowledgment to the client
    socket_io_instance.emit(
        "confirm_connect",
        {"message": "Connected to whisper core handler", "sid": request.sid},
        namespace=PROPAGATE_WHISPER_EVENTS_NAMESPACE,
    )


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #


# /whispercore/status
@whisper_core_bp.route("/status", methods=["POST"])
def handle_status():
    """
    Check the status of the whisper core handler.
    """

    # retrieve status from the request
    status = request.json.get("status", None)
    if status is None:
        app.logger.error("No status provided in the request.")
        return jsonify({"error": "No status provided"}), 400

    # propagate the status to the client side
    try:
        socket_io_instance.emit(
            "status_update",
            {"status": status},
            namespace=PROPAGATE_WHISPER_EVENTS_NAMESPACE,
        )
    except Exception as e:
        app.logger.error(f"Error propagating status: {e}")
        return jsonify({"error": "Failed to propagate status"}), 500

    print(f"[STATUS] Whisper core handler status: {status}")
    return jsonify({"status": "success"}), 200


# /whispercore/segment_update
@whisper_core_bp.route("/segment_update", methods=["POST"])
def handle_segment_update():
    """
    Handle segment updates from the whisper core handler.

    This route is used to receive segment updates and propagate them to the client.

    @request: The Flask request object containing the segment update data.
    {
        "start_time": float,  # The start time of the segment in seconds
        "end_time": float,  # The end time of the segment in seconds
        "transcription": str,  # The transcription text for the segment
    }
    """
    data = request.json
    if not data:
        app.logger.error("No data provided in the request.")
        return jsonify({"error": "No data provided"}), 400

    # propagate the segment update to the client side
    socket_io_instance.emit(
        "segment_update",
        data,
        namespace=PROPAGATE_WHISPER_EVENTS_NAMESPACE,
    )

    print(f"[SEGMENT UPDATE] Received segment update: {data}")

    return jsonify({"status": "success"}), 200


# /whispercore/segment_creation
@whisper_core_bp.route("/segment_creation", methods=["POST"])
def handle_segment_creation():
    """
    Handle segment creation events from the whisper core handler.

    This route is used to receive segment creation events and propagate them to the client.
    """
    data = request.json
    if not data:
        app.logger.error("No data provided in the request.")
        return jsonify({"error": "No data provided"}), 400

    # propagate the segment creation event to the client side
    socket_io_instance.emit(
        "segment_creation",
        data,
        namespace=PROPAGATE_WHISPER_EVENTS_NAMESPACE,
    )

    print(f"[SEGMENT CREATION] Received segment creation event: {data}")

    return jsonify({"status": "success"}), 200


# /whispercore/session_completion
@whisper_core_bp.route("/session_completion", methods=["POST"])
def handle_session_completion():
    """
    Handle session completion events from the whisper core handler.

    This route is used to receive session completion events and propagate them to the client.
    """
    data = request.json
    if not data:
        app.logger.error("No data provided in the request.")
        return jsonify({"error": "No data provided"}), 400

    # propagate the session completion event to the client side
    socket_io_instance.emit(
        "session_completion",
        data,
        namespace=PROPAGATE_WHISPER_EVENTS_NAMESPACE,
    )

    print(f"[SESSION COMPLETION] Received session completion event: {data}")
    # print out all text segments
    command_gemini = ""
    if "messages" in data:
        for message in data["messages"]:
            command_gemini += f"{message}"
            print(f"Segment: {message}")

    if command_gemini:
        try:
            response = requests.post(
                "http://localhost:5001/query",
                json={"query": command_gemini}
            )
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error sending request to /query: {e}")
            return jsonify({"error": "Failed to send request to /query"}), 500

    return jsonify({"status": "success"}), 200
