# 06-20-2025_jarvis-but-for-real
mega cool project. we cooked fr fr.

# Project Setup Guide

Welcome to the Speech-To-Text Hackathon Project! This guide will help you get the project running on your machine.

## Prerequisites

### Required Software
- **Python 3.10** (required)
- **Git** (to clone the repository)

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

HOST=localhost
PORT=5000

```

### 3. Run the Setup Script


### 1. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```


## API Endpoints

Once running, the server provides these main endpoints:

- **STT API**: `/stt/*` - Speech-to-text functionality
- **Storage API**: `/storage/*` - Database operations
- **Streaming API**: `/streaming/*` - Real-time audio streaming


## Development

- The main application is in [`backend/main.py`](backend/main.py)
- API blueprints are in the [`backend/api/`](backend/api/) directory
- Database models are in [`backend/models/`](backend/models/)
- The setup script [`backend/setup.sh`](backend/setup.sh) handles most configuration automatically
