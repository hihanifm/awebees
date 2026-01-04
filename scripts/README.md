# Scripts

Scripts to manage Awebees frontend and backend services.

## Usage

### Start Services

```bash
./scripts/start.sh
```

Starts both frontend (port 5000) and backend (port 5001) as background processes.

**Requirements:**
- Backend: Python virtual environment should be created in `backend/venv` (or dependencies installed globally)
- Frontend: Node.js dependencies should be installed (`npm install` in the frontend directory)

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

## Files

- `.pids` - Stores process IDs (auto-generated, not committed to git)
- `backend.log` - Backend service logs (auto-generated)
- `frontend.log` - Frontend service logs (auto-generated)

## Notes

- The scripts track process IDs in `scripts/.pids`
- Logs are written to `scripts/backend.log` and `scripts/frontend.log`
- If services are already running, `start.sh` will exit with an error
- Services can be started/stopped independently if needed (manual process management)

