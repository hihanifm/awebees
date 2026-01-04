# Backend

FastAPI backend for Awebees Log Analyzer.

## Setup

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:5001`

API documentation available at `http://localhost:5001/docs`

