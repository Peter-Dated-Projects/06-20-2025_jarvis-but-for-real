import flask_cors
from flask import Flask, request, jsonify, Blueprint, redirect, url_for
from flask_socketio import SocketIO, emit
import asyncio
import sys
import os
import dotenv
import atexit
import threading

# Add the MCP client directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_function', 'client'))
from mcp_function.client.client import MCPClient

from backend import SocketIOInstance, AudioBuffersInstance

from api.stt import stt_bp
from api.streaming import streaming_bp

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

async def setup_mcp(app):
    """Initialize MCP client and attach to app."""
    app.mcp_client = MCPClient()
    await app.mcp_client.connect_to_servers()

def run_async_loop(loop):
    """Target for the asyncio background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

def cleanup_on_shutdown(app):
    """Cleanup MCP client and stop the event loop on shutdown."""
    if hasattr(app, 'mcp_client'):
        print("Shutting down MCP client...")
        coro = app.mcp_client.cleanup()
        future = asyncio.run_coroutine_threadsafe(coro, app.mcp_loop)
        try:
            future.result(timeout=5)
            print("MCP client cleaned up successfully.")
        except Exception as e:
            print(f"Error during MCP client cleanup: {e}")

    if hasattr(app, 'mcp_loop') and app.mcp_loop.is_running():
        print("Stopping asyncio event loop...")
        app.mcp_loop.call_soon_threadsafe(app.mcp_loop.stop)

# --------------------------------------------------------------------------- #
# Register blueprints + objects
# --------------------------------------------------------------------------- #

if __name__ == "__main__":

    app = create_app()

    with app.app_context():
        # register blue prints
        app.register_blueprint(stt_bp, url_prefix="/stt")
        app.register_blueprint(streaming_bp, url_prefix="/streaming")

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
        
        # Initialize and run the asyncio event loop in a background thread
        mcp_loop = asyncio.new_event_loop()
        app.mcp_loop = mcp_loop
        loop_thread = threading.Thread(target=run_async_loop, args=(mcp_loop,), daemon=True)
        loop_thread.start()
        
        # Run MCP setup in the background loop
        future = asyncio.run_coroutine_threadsafe(setup_mcp(app), mcp_loop)
        future.result() # Wait for setup to complete before starting Flask
        
        atexit.register(lambda: cleanup_on_shutdown(app))

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
        
    @app.route("/query", methods=["POST"])
    def query():
        user_input = request.json.get("query")
        if not user_input:
            return jsonify({"error": "Missing query parameter."}), 400

        if not hasattr(app, 'mcp_client') or not hasattr(app, 'mcp_loop'):
            return jsonify({"error": "MCP client or event loop not initialized."}), 500

        try:
            # Create a coroutine for the query
            coro = app.mcp_client.process_query(user_input)
            
            # Submit the coroutine to the running event loop from the current thread
            future = asyncio.run_coroutine_threadsafe(coro, app.mcp_loop)
            
            # Wait for the result from the other thread (with a timeout)
            llm_output = future.result(timeout=60)
            
            return jsonify({"response": llm_output})
        except Exception as e:
            return jsonify({"error": f"Error processing query: {str(e)}"}), 500

    @app.route("/cleanup", methods=["POST"])
    def cleanup_mcp():
        """Cleanup MCP client connections."""
        if hasattr(app, 'mcp_client'):
            try:
                coro = app.mcp_client.cleanup()
                future = asyncio.run_coroutine_threadsafe(coro, app.mcp_loop)
                future.result(timeout=5)
                delattr(app, 'mcp_client')
                return jsonify({"status": "success", "message": "MCP client cleaned up successfully"})
            except Exception as e:
                return jsonify({"error": f"Error during cleanup: {str(e)}"}), 500
        return jsonify({"status": "success", "message": "No MCP client to cleanup"})

    # ----------------------------------------------------------------------------- #
    # Run App
    # ----------------------------------------------------------------------------- #

    socket_io_instance = SocketIOInstance.get_instance()

    print(
        f"Starting {app.config['NAME']} v{app.config['VERSION']} on {os.getenv('BACKEND_HOST', 'localhost')}:{os.getenv('BACKEND_PORT', 5000)}"
    )

    socket_io_instance.init_app(app)
    socket_io_instance.run(
        app,
        host=os.getenv("BACKEND_HOST", "localhost"),
        port=os.getenv("BACKEND_PORT", 5000),
        debug=os.getenv("DEBUG", True),
        use_reloader=False,
    )

