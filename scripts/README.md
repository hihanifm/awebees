# Scripts

Scripts to manage Awebees frontend and backend services.

## Usage

### Initial Setup (Run Once)

```bash
./scripts/setup.sh
```

Sets up the project for the first time:
- Creates Python virtual environment in `backend/venv`
- Installs Python dependencies
- Installs Node.js dependencies
- Creates `.env` files from `.env.example` templates

### Start Services

```bash
./scripts/start.sh
```

Starts both frontend (port 34000) and backend (port 34001) as background processes.

**Requirements:**
- Backend: Python virtual environment should be created in `backend/venv` (or dependencies installed globally)
- Frontend: Node.js dependencies should be installed (`npm install` in the frontend directory)

**Error Handling:**
- The script checks if services start successfully and displays error messages if they fail
- Common errors (missing dependencies, port conflicts, startup failures) are detected and reported
- Check the log files for detailed error information

### Check Status

```bash
./scripts/status.sh
```

Shows whether frontend and backend services are running.

### Stop Services

```bash
./scripts/stop.sh
```

Stops both frontend and backend services.

### View Logs

```bash
./scripts/logs.sh          # Show frontend logs (default)
./scripts/logs.sh -f       # Show frontend logs
./scripts/logs.sh -b       # Show backend logs
```

Shows the last 10 lines of frontend or backend logs. Defaults to frontend logs.

## Logs

All logs are stored in the `scripts/` directory:

- **Backend logs**: `scripts/backend.log`
  - Contains all backend server logs (startup, requests, errors)
  - Includes FastAPI/uvicorn output and application logs
  
- **Frontend logs**: `scripts/frontend.log`
  - Contains Next.js development server logs (startup, build, errors)
  - Includes compilation errors and runtime errors

- **PID file**: `scripts/.pids`
  - Stores process IDs for tracking running services
  - Auto-generated, not committed to git

## Troubleshooting

### Port Already in Use

If you get errors about ports being in use:

1. Check what's using the port:
   ```bash
   lsof -i :5000  # Frontend port
   lsof -i :5001  # Backend port
   ```

2. Change the port in `.env` files:
   - Backend: Edit `backend/.env` and change `PORT=5001` to another port
   - Frontend: Edit `frontend/.env.local` and change `PORT=5000` to another port
   - Update `NEXT_PUBLIC_API_URL` in `frontend/.env.local` if backend port changed
   - Update `FRONTEND_URL` in `backend/.env` if frontend port changed

3. Common issue: Port 5000 on macOS is often used by Apple AirPlay. Use port 5002, 3000, or another available port.

### Services Not Starting

1. Check the logs:
   ```bash
   ./scripts/logs.sh        # Frontend logs (default)
   ./scripts/logs.sh -b     # Backend logs
   ```

2. Verify dependencies are installed:
   ```bash
   cd backend && source venv/bin/activate && pip list
   cd frontend && npm list --depth=0
   ```

3. Check if services are actually running:
   ```bash
   ./scripts/status.sh
   ps aux | grep -E "(uvicorn|next dev)"
   ```

## Notes

- The scripts track process IDs in `scripts/.pids`
- Logs are written to `scripts/backend.log` and `scripts/frontend.log`
- If services are already running, `start.sh` will exit with an error
- Services can be started/stopped independently if needed (manual process management)
