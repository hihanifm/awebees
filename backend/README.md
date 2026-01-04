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

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

Environment variables are defined in `.env` file (see `.env.example` for reference):

- `PORT` - Server port (default: 34001)
- `HOST` - Server host (default: 0.0.0.0)
- `FRONTEND_URL` - Frontend URL for CORS (default: http://localhost:34000)
- `LOG_LEVEL` - Logging level (default: INFO)

## Running

Start the server:
```bash
uvicorn app.main:app --reload
```

Or use the port from environment:
```bash
uvicorn app.main:app --reload --port ${PORT:-5001}
```

The API will be available at `http://localhost:34001` (or the port specified in `.env`)

API documentation available at `http://localhost:34001/docs`
