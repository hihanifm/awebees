# Awebees - Android Log Analyzer

A local web application for analyzing Android log files with a plugin-based insight system.

## Architecture

- **Frontend**: Next.js App Router + TypeScript + shadcn/ui + Tailwind CSS (Port 5000)
- **Backend**: FastAPI + Python (Port 5001)

## Quick Start

### Prerequisites

- Python 3.x
- Node.js and npm
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd awebees
   ```

2. Setup Backend:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   cd ..
   ```

3. Setup Frontend:
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   cd ..
   ```

4. Start Services:
   ```bash
   ./scripts/start.sh
   ```

5. Check Status:
   ```bash
   ./scripts/status.sh
   ```

6. Stop Services:
   ```bash
   ./scripts/stop.sh
   ```

## Configuration

### Environment Variables

Both frontend and backend use environment variables for configuration:

- **Backend**: See `backend/.env.example` - Copy to `backend/.env`
- **Frontend**: See `frontend/.env.example` - Copy to `frontend/.env.local`

Default ports:
- Frontend: 5000
- Backend: 5001

## Development

- Backend API docs: http://localhost:5001/docs
- Frontend: http://localhost:5000

## Project Structure

```
awebees/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── scripts/          # Management scripts
└── .cursor/          # Cursor IDE rules
```

