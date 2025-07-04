# S.O.N.A.
## Semantic Operational & Natural Assistant
mega cool project. we cooked fr fr. lowkey was like talking about how siri is poo so we built something that is better and can be integrated natively into systems, triggered by vocal commands.

# Project Setup Guide

## Prerequisites

### Required Software

-   **Python 3.10** (required)
-   **Git** (to clone the repository)

### Check Python Version

```bash
python3 --version
# Should output: Python 3.10.x
```

If you don't have Python 3.10, download it from [python.org](https://www.python.org/downloads/).

## Setup Instructions

### 1. Clone the Repository

```bash
git clone this the repo? https://github.com/Peter-Dated-Projects/06-20-2025_jarvis-but-for-real
cd 06-20-2025_jarvis-but-for-real
```

### 2. Create Environment File

Create a [`.env`](.env) file in the project root directory with the following configuration:

```env
# .env file for backend

PVPORCUPINE_API=
GEMINI_API=
WHISPER_MODEL_FILE="assets/models/ggml-medium.en.bin"
NEXT_PUBLIC_BACKEND_PORT=
NEXT_PUBLIC_BACKEND_URL=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=https://localhost:8080/callback
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

HOST=localhost
PORT=5001

```

### 3. Run the Setup Script

### 1. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Running Locally

## Backend
```bash
cd backend
python main.py
```

## Frontend
```bash
cd frontend
npm i
npm run dev
```

## API Endpoints

Once running, the server provides these main endpoints:

-   **STT API**: `/stt/*` - Speech-to-text functionality
-   **Storage API**: `/storage/*` - Database operations
-   **Streaming API**: `/streaming/*` - Real-time audio streaming

## Development

-   The main application is in [`backend/main.py`](backend/main.py)
-   API blueprints are in the [`backend/api/`](backend/api/) directory
-   Database models are in [`backend/models/`](backend/models/)
-   The setup script [`backend/setup.sh`](backend/setup.sh) handles most configuration automatically
