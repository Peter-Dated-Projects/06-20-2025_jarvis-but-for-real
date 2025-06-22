import time
import flask_cors
from flask import Flask, request, jsonify, Blueprint, redirect, url_for
from flask_socketio import SocketIO, emit

from backend import SocketIOInstance, ClientHandlerObject, SoftwareHandlerObject

from api.stt import stt_bp
from api.streaming import streaming_bp
from api.whispercorehandler import whisper_core_bp

import threading

import os
import dotenv

from source import whispercore_main, sesame_main

# ---------------------------------------------------------------------------- #

# load environment variables
dotenv.load_dotenv("../.env")

# --------------------------------------------------------------------------- #
# Flask app
# --------------------------------------------------------------------------- #

NAME = "Speech-To-Text by Peter"


def create_app():
    app = Flask(__name__, static_folder="static")
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False
    app.config["JSONIFY_MIMETYPE"] = "application/json"
    app.config["CORS_HEADERS"] = "Content-Type"
    flask_cors.CORS(app, resources={r"/*": {"origins": "*"}})
    return app


# --------------------------------------------------------------------------- #
# Register blueprints + objects
# --------------------------------------------------------------------------- #

if __name__ == "__main__":

    app = create_app()

    with app.app_context():
        # register blue prints
        app.register_blueprint(stt_bp, url_prefix="/stt")
        app.register_blueprint(streaming_bp, url_prefix="/streaming")
        app.register_blueprint(whisper_core_bp, url_prefix="/whispercore")

        # -------------------------------------------------- #
        # register custom objects
        # -------------------------------------------------- #

        # general info
        app.config["NAME"] = NAME
        app.config["VERSION"] = "0.0.1"
        app.config["DESCRIPTION"] = "Speech-To-Text API by Peter"
        app.config["AUTHOR"] = "peterzhang2427@gmail.com"

        # architecutre info
        app.config["BASE_ARCHITECTURE"] = "whisper.cpp"
        app.config["BASE_ARCHITECTURE_GITHUB"] = (
            "https://github.com/ggml-org/whisper.cpp"
        )

        # model info
        app.config["LOADED_MODELS"] = {}
        app.config["SUPPORTED_MODELS"] = [
            "tiny",
            "base",
            "base.en",  # 100% sure this one exists
            "small",
            "medium",
            "medium.en",
            "large-v1",
            "large-v2",  # idk why you'd want to run this one though
        ]

        app.config["WHISPER_LOGS"] = True
        app.config["WHISPER_LOGS_DIR"] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "logs"
        )
        app.config["WHISPER_MODELS_DIR"] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "assets", "models"
        )

        app.config["AUDIO_CACHE_DIR"] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "static", "audio"
        )

        app.config["MODEL_PATH_MAP"] = {
            # "tiny": "tiny.bin",
            # "base": "base.bin",
            "base.en": os.path.join(
                app.config["WHISPER_MODELS_DIR"], "ggml-base.en.bin"
            ),
            # "small": os.path.join(app.config["WHISPER_MODELS_DIR"], "ggml-small.bin"),
            # "medium": os.path.join(app.config["WHISPER_MODELS_DIR"], "ggml-medium.bin"),
            # "medium.en": os.path.join(
            #     app.config["WHISPER_MODELS_DIR"], "ggml-medium.en.bin"
            # ),
            # "large-v1": os.path.join(
            #     app.config["WHISPER_MODELS_DIR"], "ggml-large-v1.bin"
            # ),
            # "large-v2": os.path.join(
            #     app.config["WHISPER_MODELS_DIR"], "ggml-large-v2.bin"
            # )
        }

    # --------------------------------------------------------------------------- #
    # Routes
    # --------------------------------------------------------------------------- #

    @app.route("/test", methods=["GET"])
    def test():
        """Test route."""

        return jsonify(
            {
                "status": "success",
                "message": "This is a test route.",
                "name": app.config["NAME"],
                "version": app.config["VERSION"],
            }
        )

    @app.route("/", methods=["GET"])
    def index():
        """Index route."""

        return """
            <html>
              <body>

              <div>
                <h2>Create New Collection</h2>
                <form action="/submit_collection" method="post">
                    <label for="new_collection">Collection Name:</label>
                    <input type="text" id="new_collection" name="new_collection" required>
                    <button type="submit">Create Collection</button>
                </form>
              </div>
            <h2>Enter Your Name</h2>
                <form action="/submit" method="post">
                <label for="collection">Collection Name:</label>
                <select id="collection" name="collection">

                <div>Empty for now</div>


                </select><br><br>
                <label for="first_name">First Name:</label>
                <input type="text" id="first_name" name="first_name"><br><br>
                <label for="last_name">Last Name:</label>
                <input type="text" id="last_name" name="last_name"><br><br>
                <input type="submit" value="Submit">
            </form>
            <div>
                <h2>PostgreSQL Tables</h2>
                <ul>
                    Nothing so far
                </ul>
            </div>
            <div>
                <h2>Stored Names</h2>
                <ul>
                    Nothing so far
                </ul>
            </div>
              </body>
            </html>
        """

    # ----------------------------------------------------------------------------- #
    # Run App
    # ----------------------------------------------------------------------------- #

    GLOBAL_ARGS = {
        # mic
        "enable_mic": True,
        "mic_mutex": threading.RLock(),
        # whispercore
        "enable_whispercore": True,
        "whispercore_mutex": threading.RLock(),
        # wake word
        "wake_word_detected": False,
        "wake_word_mutex": threading.RLock(),
        # ---
        # ---
        # for thread -- disables duplicates
        "threads_mutex": threading.RLock(),
    }

    whispercore_thread = threading.Thread(
        target=whispercore_main.run_whisper_core,
        args=(GLOBAL_ARGS,),
        daemon=True,
    )
    whispercore_thread.start()

    socket_io_instance = SocketIOInstance.get_instance()

    print(
        f"Starting {app.config['NAME']} v{app.config['VERSION']} on {os.getenv('BACKEND_HOST', 'localhost')}:{os.getenv('BACKEND_PORT', 5001)}"
    )

    socket_io_instance.init_app(app)
    socket_io_instance.run(
        app,
        host=os.getenv("BACKEND_HOST", "localhost"),
        port=int(os.getenv("BACKEND_PORT", 5001)),  # Ensure port is an integer
        debug=False,
        allow_unsafe_werkzeug=True,  # Add this line
    )
