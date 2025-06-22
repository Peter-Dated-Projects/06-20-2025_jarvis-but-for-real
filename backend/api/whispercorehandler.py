from flask import Blueprint, request, jsonify

from flask import current_app as app
from backend import (
    SocketIOInstance,
    ClientHandlerObject,
)

import os


# --------------------------------------------------------------------------- #
# blueprint + constants
# --------------------------------------------------------------------------- #

whisper_core_bp = Blueprint("whisper_core_bp", __name__)


PROPAGATE_WHISPER_EVENTS_NAMESPACE = "/propagate_whisper_events"


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
        SocketIOInstance.get_instance().emit(
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
    SocketIOInstance.get_instance().emit(
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
    SocketIOInstance.get_instance().emit(
        "segment_creation",
        data,
        namespace=PROPAGATE_WHISPER_EVENTS_NAMESPACE,
    )

    print(f"[SEGMENT CREATION] Received segment creation event: {data}")

    return jsonify({"status": "success"}), 200