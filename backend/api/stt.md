

# STT API Documentation

This document describes the HTTP endpoints provided by `stt.py`.

---

## GET `/stt/status`

**Description:**  
Check whether the specified Whisper model is loaded and the STT service is available.

**Query Parameters:**
- `model` `(string, required)`  
  The key/name of the model to check in `app.config["LOADED_MODELS"]`.

**Responses:**  
- **200 OK**  
  ```json
  {
    "status": "STT service is running",
    "model": "<model_name>"
  }
  ```
- **400 Bad Request**  
  ```json
  {
    "error": "No model specified"
  }
  ```
  or
  ```json
  {
    "error": "Model not loaded",
    "model": "<model_name>"
  }
  ```

---

## POST `/stt/init`

**Description:**  
Initialize and load a Whisper model into memory for transcription.

**Request Body (JSON):**
```json
{
  "model": "<model_key>"
}
```
- **model** `(string, required)`  
  The key identifying the model in `app.config["MODEL_PATH_MAP"]`.

**Responses:**  
- **200 OK**  
  ```json
  {
    "message": "STT service initialized",
    "model": "<model_key>"
  }
  ```
  or if already loaded:
  ```json
  {
    "error": "Model already initialized",
    "model": "<model_key>",
    "loaded_models": { ... }
  }
  ```
- **400 Bad Request**  
  ```json
  {
    "error": "No model specified",
    "supported_models": [ ... ]
  }
  ```
- **500 Internal Server Error**  
  ```json
  {
    "error": "Model failed to load"
  }
  ```

---

## POST `/stt/clean`

**Description:**  
Unload one or more Whisper models from memory, or unload all.

**Query Parameters (ignore-case):**
- `model` `(list of strings)`  
  One or more model keys to unload.
- `all` `(boolean)`  
  If true, unload all loaded models.

**Responses:**  
- **200 OK**  
  ```json
  {
    "message": "STT service cleaned up",
    "model": [ ... ],
    "all_models": <true|false>
  }
  ```
- **400 Bad Request**  
  ```json
  {
    "error": "Model must be a list"
  }
  ```

---

## POST `/stt/transcribe_stream`

**Description:**  
Process a saved WAV audio file (associated with a streaming session) and return transcription segments.

**Request Body (JSON):**
```json
{
  "model": "<model_key>",
  "streaming_id": "<session_id>",
  "auto_load_model": <true|false>
}
```
- **model** `(string, required if auto_load_model is true)`  
  The model key to use for transcription.
- **streaming_id** `(string, required)`  
  Identifier corresponding to the saved audio file `<streaming_id>.wav`.
- **auto_load_model** `(boolean, optional, default=false)`  
  Whether to load the model if not already loaded.

**Responses:**  
- **200 OK**  
  ```json
  {
    "segments": [
      [ start_time, end_time, "transcribed text" ],
      ...
    ]
  }
  ```
- **400 Bad Request**  
  ```json
  {
    "error": "No audio file provided"
  }
  ```

---

## POST `/stt/debug_transcribe_file`

**Description:**  
Transcribe a specified local audio file for debugging purposes.

**Query Parameters:**
- `model` `(string, required)`  
  The loaded model key.
- `audio_file` `(string, required)`  
  Path to the audio file to transcribe.
- `language` `(string, optional)`  
  Language hint for the transcription.

**Responses:**  
- **200 OK**  
  ```json
  {
    "transcription": [
      [ start_time, end_time, "text" ],
      ...
    ]
  }
  ```
- **400 Bad Request**  
  ```json
  {
    "error": "No audio file provided"
  }
  ```
  or
  ```json
  {
    "error": "Model not loaded",
    "model": "<model_key>"
  }
  ```