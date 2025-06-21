# Backend API Documentation

This document provides a comprehensive guide to the backend API endpoints and WebSocket events used in the JARVIS application.

## Table of Contents
- Streaming API
- Speech-to-Text API
- Storage API

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

---

## Storage API

The Storage API provides database access for storing and retrieving application data.

### Utility Functions

#### `get_db_objects(filter, collection_name)`
- **Purpose**: Retrieves objects from MongoDB matching a filter.
- **Parameters**: 
  - `filter` (dict) - MongoDB query filter
  - `collection_name` (string) - Collection to query
- **Returns**: List of objects or None

#### `get_db_object_count(filter_criteria, collection_name)`
- **Purpose**: Counts objects in a collection matching criteria.
- **Parameters**:
  - `filter_criteria` (dict) - MongoDB query filter
  - `collection_name` (string) - Collection to count in
- **Returns**: Integer count

#### `ensured_endpoint(collection_name)`
- **Purpose**: Ensures a collection exists, creating it if needed.
- **Parameters**: `collection_name` (string) - The collection to check/create
- **Returns**: Boolean indicating if collection existed

### HTTP Endpoints

#### `GET /storage/status`
- **Purpose**: Verifies MongoDB connection is working.
- **Parameters**: None
- **Returns**:
  ```json
  {
    "status": "ok"
  }
  ```
- **Summary**: Simple health check for the database connection.

**Example Input:**
```http
GET /storage/status
```
**Example Output:**
```json
{
  "status": "ok"
}
```

#### `POST /storage/upload`
- **Purpose**: Inserts data into a MongoDB collection.
- **Parameters**:
  ```json
  {
    "collection": "users",
    "object": {
      "username": "jarvis_user",
      "email": "user@example.com"
    }
  }
  ```
- **Returns**:
  ```json
  {
    "status": "ok"
  }
  ```
- **Summary**: Stores one or more documents in the specified collection.

**Example Input:**
```json
{
  "collection": "users",
  "object": {
    "username": "jarvis_user",
    "email": "user@example.com"
  }
}
```
**Example Output:**
```json
{
  "status": "ok"
}
```

#### `DELETE /storage/delete`
- **Purpose**: Deletes data from MongoDB.
- **Parameters**:
  ```json
  {
    "type": "object",
    "collection": "users",
    "filter": {
      "username": "test_user"
    }
  }
  ```
- **Returns**:
  ```json
  {
    "status": "ok",
    "message": "Deleted 1 objects"
  }
  ```
- **Summary**: Removes collections or documents matching specified criteria.

**Example Input:**
```json
{
  "type": "object",
  "collection": "users",
  "filter": {
    "username": "test_user"
  }
}
```
**Example Output:**
```json
{
  "status": "ok",
  "message": "Deleted 1 objects"
}
```

#### `POST /storage/get_objects`
- **Purpose**: Retrieves objects from MongoDB.
- **Parameters**:
  ```json
  {
    "collection": "users",
    "filter": {
      "is_active": true
    }
  }
  ```
- **Returns**:
  ```json
  {
    "status": "ok",
    "objects": [
      {
        "_id": {"$oid": "123456789"},
        "username": "jarvis_user",
        "email": "user@example.com"
      }
    ]
  }
  ```
- **Summary**: Queries the database and returns matching documents.

**Example Input:**
```json
{
  "collection": "users",
  "filter": {
    "is_active": true
  }
}
```
**Example Output:**
```json
{
  "status": "ok",
  "objects": [
    {
      "_id": {"$oid": "123456789"},
      "username": "jarvis_user",
      "email": "user@example.com"
    }
  ]
}
```

#### `GET /storage/get_conversations`
- **Purpose**: Retrieves all conversations for a specific user.
- **Parameters**: `user_id` (query string) - The user ID
- **Returns**:
  ```json
  {
    "status": "ok",
    "conversations": [
      {
        "_id": {"$oid": "123456789"},
        "title": "First Conversation",
        "description": "Testing Jarvis"
      }
    ]
  }
  ```
- **Summary**: Gets all conversations associated with a user ID.
- **Example**: `GET /storage/get_conversations?user_id=5f8d43e1e6b2c87d5e8b456a`

**Example Input:**
```http
GET /storage/get_conversations?user_id=5f8d43e1e6b2c87d5e8b456a
```
**Example Output:**
```json
{
  "status": "ok",
  "conversations": [
    {
      "_id": {"$oid": "123456789"},
      "title": "First Conversation",
      "description": "Testing Jarvis"
    }
  ]
}
```

#### `POST /storage/create_conversation`
- **Purpose**: Creates a new conversation record.
- **Parameters**:
  ```json
  {
    "user_id": "5f8d43e1e6b2c87d5e8b456a",
    "data": {
      "title": "New Conversation",
      "description": "Testing with Jarvis",
      "audio_data": null,
      "created_at": "2025-06-20T14:30:00Z",
      "updated_at": "2025-06-20T14:30:00Z"
    }
  }
  ```
- **Returns**:
  ```json
  {
    "status": "ok",
    "_id": {"$oid": "123456789"},
    "title": "New Conversation",
    "description": "Testing with Jarvis",
    "updated_at": {"$date": "2025-06-20T14:30:00Z"}
  }
  ```
- **Summary**: Creates a new conversation and associates it with a user.

**Example Input:**
```json
{
  "user_id": "5f8d43e1e6b2c87d5e8b456a",
  "data": {
    "title": "New Conversation",
    "description": "Testing with Jarvis",
    "audio_data": null,
    "created_at": "2025-06-20T14:30:00Z",
    "updated_at": "2025-06-20T14:30:00Z"
  }
}
```
**Example Output:**
```json
{
  "status": "ok",
  "_id": {"$oid": "123456789"},
  "title": "New Conversation",
  "description": "Testing with Jarvis",
  "updated_at": {"$date": "2025-06-20T14:30:00Z"}
}
```

#### `POST /storage/create_user`
- **Purpose**: Creates a new user account.
- **Parameters**:
  ```json
  {
    "first_name": "Test",
    "last_name": "User",
    "email": "test.user@example.com",
    "password": "securepassword123",
    "created_at": "2025-06-20T14:00:00Z",
    "updated_at": "2025-06-20T14:00:00Z",
    "is_active": true
  }
  ```
- **Returns**:
  ```json
  {
    "status": "ok",
    "id": "5f8d43e1e6b2c87d5e8b456a"
  }
  ```
- **Summary**: Registers a new user in the system.

**Example Input:**
```json
{
  "first_name": "Test",
  "last_name": "User",
  "email": "test.user@example.com",
  "password": "securepassword123",
  "created_at": "2025-06-20T14:00:00Z",
  "updated_at": "2025-06-20T14:00:00Z",
  "is_active": true
}
```
**Example Output:**
```json
{
  "status": "ok",
  "id": "5f8d43e1e6b2c87d5e8b456a"
}
```