

# Streaming API Documentation

This document describes the WebSocket events and HTTP endpoints provided by `streaming.py`.

---

## WebSocket Namespace: `/streaming`

All events use the `/streaming` namespace. Clients must connect via Socket.IO.

### Event: `connect`

- **Purpose:**  
  Initialize a streaming session and allocate an audio buffer for the client.

- **Server Action:**  
  - Stores a new entry in `AudioBuffersInstance` keyed by `request.sid`.  
  - Emits `response` with a confirmation message.

- **Response Payload:**
  ```json
  {
    "message": "Connected to server"
  }
  ```

---

### Event: `audio_chunk`

- **Purpose:**  
  Send a raw audio chunk (bytes) from the client to the server for buffering.

- **Client Payload:**
  ```json
  {
    "chunk": "<binary audio data>"
  }
  ```

- **Server Action:**  
  - Appends `chunk` to `AudioBuffersInstance()[sid][CACHE_AUDIO_DATA]`.  
  - Emits `response` acknowledging receipt.

- **Response Payload:**
  ```json
  {
    "message": "received chunk"
  }
  ```

---

### Event: `stop_recording`

- **Purpose:**  
  Client signals end of streaming. Server will return the URL of the saved audio file.

- **Server Action:**  
  - Looks up the final WAV file path from `AudioBuffersInstance()`.  
  - Emits `result_file_path` with the public file URL.

- **Response Payload:**
  ```json
  {
    "streaming_id": "<sid>",
    "message": "Disconnected from server",
    "file_url": "http://<host>/static/audio/<sid>.wav"
  }
  ```

---

### Event: `disconnect`

- **Purpose:**  
  Triggered when the client disconnects unexpectedly. The server attempts to process any buffered audio.

- **Server Action:**  
  - Calls `process_audio(sid)` to convert and save the buffered data.  
  - Emits `error` if processing fails.

---

## HTTP Endpoint: `/streaming/force_stop`

- **Method:** `POST`  
- **Purpose:**  
  Force the server to stop streaming and process the audio buffer for the current session.

- **Request Context:**  
  Server-derived `request.session_id` identifies the client.

- **Server Action:**  
  1. Validates `session_id`.  
  2. Ensures the audio buffer is not empty.  
  3. Calls `process_audio` to save the audio file.

- **Success Response (200):**
  ```json
  {
    "message": "Audio processing complete"
  }
  ```

- **Error Responses:**  
  - **400 Bad Request**  
    ```json
    { "error": "Invalid streaming key" }
    ```  
    or  
    ```json
    { "error": "Audio buffer is empty" }
    ```  
  - **500 Internal Server Error**  
    ```json
    { "error": "Failed to process audio" }
    ```