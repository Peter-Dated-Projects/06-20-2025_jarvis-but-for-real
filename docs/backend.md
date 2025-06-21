# Backend API Documentation

This document provides a comprehensive guide to the backend API endpoints and WebSocket events used in the JARVIS application.

## Table of Contents
- Streaming API
- Speech-to-Text API

---

## Streaming API

The Streaming API handles real-time audio streaming via WebSockets and processes audio data for transcription.

### Utility Functions

#### `is_valid_streaming_key(key)`
- **Purpose**: Verifies if the provided streaming key exists in the audio buffers.
- **Parameters**: `key` (string) - The streaming session ID
- **Returns**: Boolean indicating if the key is valid

**Example Input:**
```python
# For is_valid_streaming_key
is_valid_streaming_key("session123")
```
**Example Output:**
```python
True
```

#### `is_audio_buffer_empty(key)`
- **Purpose**: Checks if the audio buffer for a given streaming key is empty.
- **Parameters**: `key` (string) - The streaming session ID
- **Returns**: Boolean indicating if the buffer is empty

**Example Input:**
```python
# For is_audio_buffer_empty
is_audio_buffer_empty("session123")
```
**Example Output:**
```python
False
```

#### `process_audio(key)`
- **Purpose**: Processes and saves buffered audio data to a WAV file.
- **Parameters**: `key` (string) - The streaming session ID
- **Returns**: Boolean indicating success or failure

**Example Input:**
```python
# For process_audio
process_audio("session123")
```
**Example Output:**
```python
True
```

### WebSocket Events

#### `/begin_audio_stream` - `connect`
- **Purpose**: Initializes a new audio streaming session.
- **Parameters**: 
  - `sid` (string) - Session ID (automatically provided)
  - `model` (string, optional) - The model to use for STT, defaults to `DEFAULT_MODEL`
- **Returns**: 
  ```json
  {
    "message": "Connected to server",
    "model": "assets/models/ggml-base.en.bin"
  }
  ```
- **Summary**: Establishes a new audio streaming session and allocates resources.

**Example Input:**
```javascript
// Client connects to /begin_audio_stream with (optionally) a model
socket.emit('connect', { model: "assets/models/ggml-base.en.bin" });
```
**Example Output:**
```json
{
  "message": "Connected to server",
  "model": "assets/models/ggml-base.en.bin"
}
```

#### `/streaming` - `real_time_stt_request`
- **Purpose**: Processes audio chunks for real-time speech-to-text.
- **Parameters**:
  ```json
  {
    "audio_data": "<binary audio data>",
    "real_time": true,
    "audio_format": "paInt16",
    "channels": 1,
    "sample_rate": 16000
  }
  ```
- **Returns**:
  ```json
  {
    "new_segment": true,
    "segment_start": 0,
    "segment_end": 42,
    "segment_transcript": "Transcribed text appears here"
  }
  ```
- **Summary**: Handles incoming audio data and returns real-time transcription when available.

**Example Input:**
```javascript
socket.emit('real_time_stt_request', {
  audio_data: "<binary audio data>",
  real_time: true,
  audio_format: "paInt16",
  channels: 1,
  sample_rate: 16000
});
```
**Example Output:**
```json
{
  "new_segment": true,
  "segment_start": 0,
  "segment_end": 42,
  "segment_transcript": "Transcribed text appears here"
}
```

#### `/streaming` - `stop_recording`
- **Purpose**: Finalizes recording and returns the URL to the processed audio file.
- **Parameters**: None (uses session ID)
- **Returns**:
  ```json
  {
    "streaming_id": "session123",
    "message": "Successfully stopped recording + generated audio file.",
    "file_url": "http://localhost:5000/static/audio/session123.wav"
  }
  ```
- **Summary**: Stops recording, processes the audio, and returns the audio file URL.

**Example Input:**
```javascript
socket.emit('stop_recording');
```
**Example Output:**
```json
{
  "streaming_id": "session123",
  "message": "Successfully stopped recording + generated audio file.",
  "file_url": "http://localhost:5000/static/audio/session123.wav"
}
```

#### `/streaming` - `disconnect`
- **Purpose**: Cleans up resources when client disconnects.
- **Parameters**: None (uses session ID)
- **Returns**: None
- **Summary**: Handles cleanup when client disconnects from the WebSocket.

**Example Input:**
```javascript
socket.disconnect();
```
**Example Output:**
```json
{}
```

### HTTP Endpoints

#### `POST /streaming/force_stop`
- **Purpose**: Force stops audio streaming and processes buffered audio.
- **Parameters**: Uses `request.session_id` (no JSON body needed)
- **Returns**:
  ```json
  {
    "message": "Audio processing complete"
  }
  ```
- **Summary**: Server-side mechanism to forcibly end a streaming session.

**Example Input:**
```http
POST /streaming/force_stop
// No body required. Session ID is used from authentication/session.
```
**Example Output:**
```json
{
  "message": "Audio processing complete"
}
```

---

## Speech-to-Text API

The STT API provides endpoints for managing and using speech-to-text models.

### Utility Functions

#### `is_model_valid(model)`
- **Purpose**: Checks if a model name is in the supported models list.
- **Parameters**: `model` (string) - The model name to check
- **Returns**: Boolean indicating if the model is valid

#### `is_model_loaded(model)`
- **Purpose**: Checks if a model is currently loaded in memory.
- **Parameters**: `model` (string) - The model name to check
- **Returns**: Boolean indicating if the model is loaded

#### `load_model(model)`
- **Purpose**: Loads a Whisper model into memory.
- **Parameters**: `model` (string) - The model name to load
- **Returns**: Boolean indicating success or failure

### HTTP Endpoints

#### `GET /stt/status`
- **Purpose**: Checks if a specified model is loaded and ready.
- **Parameters**: `model` (query string) - The model to check
- **Returns**:
  ```json
  {
    "status": "STT service is running",
    "model": "ggml-base.en"
  }
  ```
- **Summary**: Verifies that a specific speech-to-text model is loaded and available.
- **Example**: `GET /stt/status?model=ggml-base.en`

**Example Input:**
```http
GET /stt/status?model=ggml-base.en
```
**Example Output:**
```json
{
  "status": "STT service is running",
  "model": "ggml-base.en"
}
```

#### `POST /stt/init`
- **Purpose**: Initializes and loads a Whisper model.
- **Parameters**:
  ```json
  {
    "model": "ggml-base.en"
  }
  ```
- **Returns**:
  ```json
  {
    "message": "STT service initialized",
    "model": "ggml-base.en"
  }
  ```
- **Summary**: Loads the specified model into memory for transcription use.

**Example Input:**
```json
{
  "model": "ggml-base.en"
}
```
**Example Output:**
```json
{
  "message": "STT service initialized",
  "model": "ggml-base.en"
}
```

#### `POST /stt/clean`
- **Purpose**: Unloads models from memory to free resources.
- **Parameters**:
  ```json
  {
    "model": ["ggml-base.en", "ggml-small.en"],
    "all": false
  }
  ```
- **Returns**:
  ```json
  {
    "message": "STT service cleaned up",
    "model": ["ggml-base.en", "ggml-small.en"],
    "all_models": false
  }
  ```
- **Summary**: Releases memory by unloading specified models or all models.

**Example Input:**
```json
{
  "model": ["ggml-base.en", "ggml-small.en"],
  "all": false
}
```
**Example Output:**
```json
{
  "message": "STT service cleaned up",
  "model": ["ggml-base.en", "ggml-small.en"],
  "all_models": false
}
```

#### `POST /stt/transcribe_stream`
- **Purpose**: Transcribes a saved audio file from a streaming session.
- **Parameters**:
  ```json
  {
    "model": "ggml-base.en",
    "streaming_id": "session123",
    "auto_load_model": true
  }
  ```
- **Returns**:
  ```json
  {
    "segments": [
      [0.0, 2.56, "Hello Jarvis"],
      [2.72, 5.84, "How are you today?"]
    ]
  }
  ```
- **Summary**: Processes a previously recorded audio file and returns the transcription segments.

**Example Input:**
```json
{
  "model": "ggml-base.en",
  "streaming_id": "session123",
  "auto_load_model": true
}
```
**Example Output:**
```json
{
  "segments": [
    [0.0, 2.56, "Hello Jarvis"],
    [2.72, 5.84, "How are you today?"]
  ]
}
```

#### `POST /stt/debug_transcribe_file`
- **Purpose**: Transcribes a specific audio file for debugging.
- **Parameters**: 
  - `model` (query string) - Model to use
  - `audio_file` (query string) - Path to audio file
  - `language` (query string, optional) - Language hint
- **Returns**:
  ```json
  {
    "transcription": [
      [0.0, 2.56, "Hello Jarvis"],
      [2.72, 5.84, "How are you today?"]
    ]
  }
  ```
- **Summary**: Direct transcription of any audio file, useful for testing.
- **Example**: `POST /stt/debug_transcribe_file?model=ggml-base.en&audio_file=/path/to/file.wav`

**Example Input:**
```http
POST /stt/debug_transcribe_file?model=ggml-base.en&audio_file=/path/to/file.wav
```
**Example Output:**
```json
{
  "transcription": [
    [0.0, 2.56, "Hello Jarvis"],
    [2.72, 5.84, "How are you today?"]
  ]
}
```