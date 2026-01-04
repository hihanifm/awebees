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

2. Run setup script (one-time setup):
   ```bash
   ./scripts/setup.sh
   ```
   
   This will:
   - Create Python virtual environment
   - Install all dependencies (Python and Node.js)
   - Create `.env` files from examples

3. Start Services:
   ```bash
   ./scripts/start.sh
   ```

5. Check Status:
   ```bash
   ./scripts/status.sh
   ```

6. View Logs:
   ```bash
   ./scripts/logs.sh        # Frontend logs (default)
   ./scripts/logs.sh -b     # Backend logs
   ```

7. Stop Services:
   ```bash
   ./scripts/stop.sh
   ```

## Configuration

### Environment Variables

Both frontend and backend use environment variables for configuration:

- **Backend**: See `backend/.env.example` - Copy to `backend/.env`
- **Frontend**: See `frontend/.env.example` - Copy to `frontend/.env.local`

Default ports:
- Frontend: 34000
- Backend: 34001

## Logs

Error and application logs are stored in the `scripts/` directory:

- **Backend logs**: `scripts/backend.log`
- **Frontend logs**: `scripts/frontend.log`

View logs:
```bash
tail -f scripts/backend.log   # Backend logs
tail -f scripts/frontend.log  # Frontend logs
```

## Development

- Backend API docs: http://localhost:34001/docs
- Frontend: http://localhost:34000

## Project Structure

```
awebees/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── scripts/          # Management scripts
└── .cursor/          # Cursor IDE rules
```

