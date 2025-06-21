from flask import Blueprint, jsonify, request
from flask import current_app as app

import os
from pywhispercpp.model import Model as WhisperModel

from typing import Optional, Union, List, Dict, Any


# --------------------------------------------------------------------------- #
# blueprint
# --------------------------------------------------------------------------- #

stt_bp = Blueprint("stt_bp", __name__)


# --------------------------------------------------------------------------- #
# verification functions
# --------------------------------------------------------------------------- #


def is_model_valid(model: str) -> bool:
    """Check if the model is valid."""
    return model in app.config["MODEL_PATH_MAP"]


def is_model_loaded(model: str) -> bool:
    """Check if the model is loaded."""
    return model in app.config["LOADED_MODELS"]


def load_model(model: str) -> bool:
    """Load the model into memory."""
    # check if model already loadaed
    if is_model_loaded(model):
        return False
    if not is_model_valid(model):
        app.logger.error("Model not valid")
        return False

    # define variables
    _model_name = os.path.basename(model)

    # Load model
    _model = WhisperModel(
        app.config["MODEL_PATH_MAP"][model],
        redirect_whispercpp_logs_to=(
            f"{app.config['WHISPER_LOGS_DIR']}/{_model_name}.log"
            if app.config["WHISPER_LOGS"]
            else None
        ),
    )

    # Placeholder for loading logic
    app.config["LOADED_MODELS"][model] = _model
    app.logger.debug("Loading model: %s", model)
    return True


def get_model_path(model: str) -> str:
    """Get the model from the path."""
    if not is_model_valid(model):
        app.logger.error("Model not valid")
        return ""
    return app.config["MODEL_PATH_MAP"][model]


def compute_file_transcription(model: str, file_name: str) -> List[any]:
    print(model, file_name)
    print(app.config["MODEL_PATH_MAP"])
    print(app.config["LOADED_MODELS"])
    if not is_model_valid(model):
        print("Model not valid")
        return []
    if not is_model_loaded(model):
        print("Model not loaded")
        return []
    if not os.path.exists(file_name):
        print("File not found")
        return []

    # perform transcription
    segments = app.config["LOADED_MODELS"][model].transcribe(file_name)
    # return results
    print(segments)
    return [[segment.t0, segment.t1, segment.text] for segment in segments]


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #


@stt_bp.route("/status", methods=["GET"])
def status():
    """Check the status of the STT service."""
    _model = request.args.get("model")
    if not _model:
        return jsonify({"error": "No model specified"}), 400

    # check if model is loaded
    if not is_model_loaded(_model):
        return jsonify({"error": "Model not loaded", "model": _model}), 400

    return jsonify({"status": "STT service is running", "model": _model}), 200


@stt_bp.route("/init", methods=["POST"])
def stt_initialize():
    """Initialize the STT service."""
    # grab the model from params to use
    _model = request.json.get("model")
    if not is_model_valid(_model):
        return (
            jsonify(
                {
                    "error": "No model specified",
                    "supported_models": app.config["SUPPORTED_MODELS"],
                }
            ),
            400,
        )

    # Placeholder for any initialization logic
    app.logger.debug("Initializing STT service with model: %s", _model)

    # check if model already loaded
    if is_model_loaded(_model):
        return (
            jsonify(
                {
                    "error": "Model already loaded",
                    "model": _model,
                    "loaded_models": app.config["LOADED_MODELS"],
                }
            ),
            400,
        )

    return jsonify({"message": "STT service initialized", "model": _model}), 200


@stt_bp.route("/clean", methods=["POST"])
def stt_clean():
    """Clean up STT services."""
    _models: List[str] = request.args.get("model")
    _all_models: bool = request.args.get("all")

    app.logger.debug(f"Cleaning variables: {_models}, all: {_all_models}")

    # check if all models are loaded
    if not _all_models and not _models:
        # error
        return jsonify({"error": "Model must be a list"}), 400

    # if all models selected
    if _all_models:
        _models = app.config["SUPPORTED_MODELS"]

    # check if models are loaded
    _targets = [m for m in _models if is_model_loaded(m)]

    # clean models
    for model in _targets:
        # Placeholder for cleanup logic
        app.logger.debug("FAKE - Cleaning up model: %s", model)
        # Remove the model from loaded models
        app.config["LOADED_MODELS"].pop(model, None)

    # return results
    return jsonify(
        {
            "message": "STT service cleaned up",
            "model": _models,
            "all_models": _all_models,
        }
    )


@stt_bp.route("/transcribe_stream", methods=["POST"])
def stt_transcribe_stream():
    """Speech-to-text route."""
    _model = request.json.get("model")
    _sid = request.json.get("streaming_id")
    _auto_load_model = request.json.get("audo_load_model", False)

    # Get the audio file from the request
    print(_model, _sid)

    if not _sid:
        return jsonify({"error": "No audio file provided"}), 400

    # check if we need to load the model
    if _auto_load_model:
        # check if model is loaded
        if not is_model_loaded(_model):
            # load the model
            load_model(_model)

    # Placeholder response
    _file_path = os.path.join(app.config["AUDIO_CACHE_DIR"], f"{_sid}.wav")

    # check if request model is open
    if not is_model_valid(_model):
        return (
            jsonify(
                {
                    "error": "Model not valid",
                    "supported_models": app.config["SUPPORTED_MODELS"],
                }
            ),
            400,
        )

    # check if model is loaded
    if not is_model_loaded(_model):
        # load model
        if not load_model(_model):
            return (
                jsonify(
                    {
                        "error": "Model failed to load",
                        "model": _model,
                        "loaded_models": app.config["LOADED_MODELS"],
                    }
                ),
                500,
            )
        print("Loaded Model")
    print("Loaded models: ", app.config["LOADED_MODELS"])
    segments = compute_file_transcription(_model, _file_path)

    print("Segments:", segments)

    return jsonify({"segments": segments})


@stt_bp.route("/debug_transcribe_file", methods=["POST"])
def stt_debug_transcribe_file():
    """Debug transcribe file route."""
    _model = request.args.get("model")
    _audio_file = request.args.get("audio_file")
    _language = request.args.get("language", None)

    # check if path to an audio file is detected
    if not _audio_file:
        return jsonify({"error": "No audio file provided"}), 400

    # check if model is loaded
    # don't load if not already loaded
    if not is_model_loaded(_model):
        # load model
        if not load_model(_model):
            return (
                jsonify(
                    {
                        "error": "Model failed to load",
                        "model": _model,
                        "loaded_models": app.config["LOADED_MODELS"],
                    }
                ),
                500,
            )
    # check if model is valid
    if not is_model_valid(_model):
        return (
            jsonify(
                {
                    "error": "Model not valid",
                    "supported_models": app.config["SUPPORTED_MODELS"],
                }
            ),
            400,
        )
    print("Loaded Models: ", app.config["LOADED_MODELS"])

    # perform transcription
    segments = app.config["LOADED_MODELS"][_model].transcribe(
        _audio_file, language=_language
    )

    # return results
    return (
        jsonify(
            {
                "transcription": [
                    [segment.t0, segment.t1, segment.text] for segment in segments
                ]
            }
        ),
        200,
    )
