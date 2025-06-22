from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit

from flask import current_app as app
from backend import (
    SocketIOInstance,
    AudioBuffersInstance,
    AudioStreamCache,
    WhisperCoreSingleModel,
    JarvisBrainFactory,
)


from typing import Optional, Union, List, Dict, Any


# --------------------------------------------------------------------------- #
# blueprint + constants
# --------------------------------------------------------------------------- #

messaging_bp = Blueprint("messaging", __name__, url_prefix="/messaging")


# --------------------------------------------------------------------------- #
# messaging API
# --------------------------------------------------------------------------- #


@messaging_bp.route("/messages", methods=["GET"])
def fetch_all_messages() -> Union[List[Dict[str, Any]], Dict[str, str]]:
    """
    Fetch all messages from the database.

    @data:
    {
        "filters": Optional[str],  # Filters to apply to the messages, e.g., "unread", "starred"
        "sort_by": Optional[str],  # Field to sort by, e.g., "date", "sender"
        "sort_order": Optional[str]  # Order to sort by, e.g., "asc", "desc"
        "limit": Optional[int],
        "offset": Optional[int]
        "search": Optional[str]
    }

    Returns:
        List of messages or an error message.
    """
    try:
        instance = JarvisBrainFactory.get_instance()

        # request query w filters
        filters = request.args.get("filters", None)
        sort_by = request.args.get("sort_by", "date")
        sort_order = request.args.get("sort_order", "desc")
        limit = request.args.get("limit", None, type=int)

        # Fetch all messages with optional filters and sorting
        results = instance.fetch_all_messages(
            filters=filters, sort_by=sort_by, sort_order=sort_order, limit=limit
        )

        return jsonify({"messages": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
