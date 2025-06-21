import flask_cors
from flask import Flask, request, jsonify, Blueprint, redirect, url_for
from flask_socketio import SocketIO, emit

from backend import SocketIOInstance, AudioBuffersInstance, MongoDBInstance

from api.stt import stt_bp
from api.streaming import streaming_bp
from api.storage import storage_bp

import os
import dotenv

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
        app.register_blueprint(storage_bp, url_prefix="/storage")

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

        # add mongoengine
        mongoengine.connect(
            db=os.getenv("MONGODB_DATABASE"),
            host=os.getenv("MONGODB_URI"),
            port=int(os.getenv("MONGODB_PORT")),
            username=os.getenv("MONGODB_USERNAME"),
            password=os.getenv("MONGODB_PASSWORD"),
            authentication_source=os.getenv("MONGODB_AUTH_SOURCE"),
            authentication_mechanism=os.getenv("MONGODB_AUTH_MECHANISM"),
        )

    # --------------------------------------------------------------------------- #
    # Routes
    # --------------------------------------------------------------------------- #

    @app.route("/purge", methods=["GET"])
    def purge():
        # clean out all collections
        _client = MongoDBInstance.get_instance()
        _db = _client.get_default_database()

        _collections_list = _db.list_collection_names()
        for collection in _collections_list:
            _db.drop_collection(collection)

        # return status
        return jsonify({"status": "ok", "message": "purged all collections"}), 200

    @app.route("/test", methods=["GET"])
    def test():
        """Test route."""

        import uuid

        _client = MongoDBInstance.get_instance()
        _db = _client.get_default_database()

        # create a user object
        _user = models.user.User(
            first_name="Peter",
            last_name="Zhang",
            email=f"{uuid.uuid4()}@gmail.com",
            password="temp_password",
        )

        # create a conversation
        _c1 = models.conversation.Conversation(
            title="test",
            description="test",
            audio_data=b"emptydata",
            audio_duration=1.0,
        )
        _c1.save()

        _user.conversations.append(_c1)
        _user.save()

        # collect data
        _collections_list = _db.list_collection_names()
        _user_list = _db.get_collection("users").find({})
        _conversation_list = _db.get_collection("conversations").find({})

        return f"""
            <html>
              <body>
            <div>
                <h2>MongoDB Collections</h2>
                <ul>
                {''.join(f"<li>{collection}</li>" for collection in _collections_list)}
                </ul>
            </div>
            <div>
                <h2>Stored Names</h2>
                {
                ''.join(
                    f"<h3>{collection}</h3><ul>{''.join([f'<li>{str(x)}</li>' for x in _db.get_collection(collection).find({})])}</ul>" for collection in _collections_list
                )
                }
            </div>
              </body>
            </html>
        """

    @app.route("/", methods=["GET"])
    def index():
        """Index route."""

        _client = MongoDBInstance.get_instance()
        _db = _client.get_default_database()

        _collections_list = _db.list_collection_names()

        return f"""
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
                {''.join(f"<option value='{collection}'>{collection}</option>" for collection in _collections_list)}
                </select><br><br>
                <label for="first_name">First Name:</label>
                <input type="text" id="first_name" name="first_name"><br><br>
                <label for="last_name">Last Name:</label>
                <input type="text" id="last_name" name="last_name"><br><br>
                <input type="submit" value="Submit">
            </form>
            <div>
                <h2>MongoDB Collections</h2>
                <ul>
                {''.join(f"<li>{collection}</li>" for collection in _collections_list)}
                </ul>
            </div>
            <div>
                <h2>Stored Names</h2>
                {
                ''.join(
                    f"<h3>{collection}</h3><ul>{''.join([f'<li>{str(x)}</li>' for x in _db.get_collection(collection).find({})])}</ul>" for collection in _collections_list
                )
                }
            </div>
              </body>
            </html>
        """

    @app.route("/submit_collection", methods=["POST"])
    def submit_collection():
        # grab instance + save a new object
        _client = MongoDBInstance.get_instance()
        _db = _client.get_default_database()

        # grab data
        collection_name = request.form.get("new_collection")

        # create collection if it doesn't exist
        if collection_name not in _db.list_collection_names():
            # send an api request to /storage/upload
            _db.create_collection(collection_name)

        # redirect back to index
        return redirect(url_for("index"))

    @app.route("/submit", methods=["POST"])
    def submit():
        # grab instance + save a new object
        _client = MongoDBInstance.get_instance()
        _db = _client.get_default_database()

        # grab data
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        collection_name = request.form.get("collection")

        # create object
        _user = models.user.User(
            first_name=first_name,
            last_name=last_name,
            email="temp_email@gmail.com",
            password="temp_password",
        )

        # insert object into collection
        if not collection_name:
            _user.save()
        else:
            _collection = _db.get_collection(collection_name)
            _collection.insert_one(_user.to_mongo().to_dict())

        # redirect back to index
        return redirect(url_for("index"))

    # ----------------------------------------------------------------------------- #
    # Run App
    # ----------------------------------------------------------------------------- #

    socket_io_instance = SocketIOInstance.get_instance()

    print(
        f"Starting {app.config['NAME']} v{app.config['VERSION']} on {os.getenv('BACKEND_HOST', 'localhost')}:{os.getenv('BACKEND_PORT', 5001)}"
    )

    socket_io_instance.init_app(app)
    socket_io_instance.run(
        app,
        host=os.getenv("BACKEND_HOST", "localhost"),
        port=os.getenv("BACKEND_PORT", 5001),
        debug=os.getenv("DEBUG", True),
    )
