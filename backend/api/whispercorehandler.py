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

whisper_core_bp = Blueprint("whisper_core_bp", __name__)



# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #

# backendip:port/whispercore/status
@whisper_core_bp.route("/status", methods=["GET"])
