# Scripts

Scripts to manage Lens frontend and backend services.

Available for both **Linux/Mac** and **Windows** platforms.

## Usage

### Initial Setup (Run Once)

**Linux/Mac:**
```bash
./scripts/setup.sh
```

**Windows:**
```cmd
scripts\win-setup.bat
```

Sets up the project for the first time:
- **Automatically detects and offers to install Python and Node.js if not found** (Windows only)
- Uses `winget` (Windows Package Manager) for automatic installation
- Creates Python virtual environment in `backend/venv`
- Installs Python dependencies
- Installs Node.js dependencies
- Creates `.env` files from `.env.example` templates

**Note for Windows:** If Python or Node.js are installed during setup, you'll need to restart your command prompt and run the setup script again.

### Start Services

**Linux/Mac:**
```bash
./scripts/start.sh          # Development mode (default)
./scripts/start.sh -p       # Production mode
./scripts/start.sh --help   # Show help
```

**Windows:**
```cmd
scripts\win-start.bat          REM Development mode (default)
scripts\win-start.bat -p       REM Production mode
scripts\win-start.bat --help   REM Show help
```

Starts both frontend (port 34000) and backend (port 34001) as background processes.

**Modes:**
- **Development (default)**: Uses `next dev` with hot reload
- **Production (-p)**: Uses `next start` (requires `npm run build` first)

**Requirements:**
- Backend: Python virtual environment should be created in `backend/venv` (or dependencies installed globally)
- Frontend: Node.js dependencies should be installed (`npm install` in the frontend directory)
- Production mode: Frontend must be built first (`npm run build` in frontend directory)

**Error Handling:**
- The script checks if services start successfully and displays error messages if they fail
- Common errors (missing dependencies, port conflicts, startup failures) are detected and reported
- Check the log files for detailed error information

### Check Status

**Linux/Mac:**
```bash
./scripts/status.sh
```

**Windows:**
```cmd
scripts\win-status.bat
```

Shows whether frontend and backend services are running.

### Stop Services

**Linux/Mac:**
```bash
./scripts/stop.sh
```

**Windows:**
```cmd
scripts\win-stop.bat
```

Stops both frontend and backend services.

### View Logs

**Linux/Mac:**
```bash
./scripts/logs.sh          # Show frontend logs (default)
./scripts/logs.sh -f       # Show frontend logs
./scripts/logs.sh -b       # Show backend logs
```

**Windows:**
```cmd
scripts\win-logs.bat          REM Show frontend logs (default)
scripts\win-logs.bat -f       REM Show frontend logs
scripts\win-logs.bat -b       REM Show backend logs
```

Shows the last 20 lines of frontend or backend logs with the file path. Defaults to frontend logs.

### Test AI Configuration

**Linux/Mac:**
```bash
./scripts/test-ai-key.sh
```

**Windows:**
```cmd
scripts\win-test-ai-key.bat
```

Validates the OpenAI API configuration and connection:
- Tests if the API key is valid
- Checks if the configured model is available
- Displays configuration details
- Shows recommended models for log analysis

**What it checks:**
- `AI_ENABLED` setting
- OpenAI API key validity
- API connection and availability
- Configured model (`OPENAI_MODEL`) availability
- Lists recommended models for Lens

**Example output:**
```
🔍 Lens AI Configuration Validator
============================================================

📋 Configuration:
  AI Enabled:    True
  Base URL:      https://api.openai.com/v1
  API Key:       sk-proj-EB...k_2cdf8A
  Model:         gpt-4o-mini
  Max Tokens:    4000
  Temperature:   0.5

🔑 Testing API Key...
✅ API Key is valid!

🤖 Checking Configured Model...
✅ Model 'gpt-4o-mini' is available!

💡 Recommended Models for Lens:
  [✓] gpt-4o-mini          - Fast, cost-effective, great for log analysis
  [ ] gpt-4o               - More capable, higher quality, more expensive
  [ ] gpt-4-turbo          - Good balance of speed and capability

============================================================
✅ All checks passed! AI features are ready to use.
============================================================
```

### Version Management

**Linux/Mac:**
```bash
./scripts/version.sh get              # Show current version
./scripts/version.sh set 0.2.0        # Set version to 0.2.0
./scripts/version.sh bump major       # Bump major version (1.0.0 -> 2.0.0)
./scripts/version.sh bump minor       # Bump minor version (1.0.0 -> 1.1.0)
./scripts/version.sh bump patch       # Bump patch version (1.0.0 -> 1.0.1)
./scripts/version.sh sync             # Sync version to package.json
```

**Windows:**
```cmd
scripts\win-version.bat get              REM Show current version
scripts\win-version.bat set 0.2.0        REM Set version to 0.2.0
scripts\win-version.bat bump major       REM Bump major version (1.0.0 -> 2.0.0)
scripts\win-version.bat bump minor       REM Bump minor version (1.0.0 -> 1.1.0)
scripts\win-version.bat bump patch       REM Bump patch version (1.0.0 -> 1.0.1)
scripts\win-version.bat sync             REM Sync version to package.json
```

Manages the application version stored in `VERSION` file at the project root. This is the single source of truth for the application version.

**Version Management:**
- Version is stored in `VERSION` file at project root
- The `version.sh` script can sync the version to `frontend/package.json`
- The backend reads the version from the `VERSION` file and exposes it via `/api/version` endpoint
- Use semantic versioning (MAJOR.MINOR.PATCH format)

## Logs

All logs are stored in the `logs/` directory at the project root:

- **Backend logs**: `logs/backend.log`
  - Contains all backend server logs (startup, requests, errors)
  - Includes FastAPI/uvicorn output and application logs
  
- **Frontend logs**: `logs/frontend.log`
  - Contains Next.js development server logs (startup, build, errors)
  - Includes compilation errors and runtime errors

- **PID file**: `scripts/.pids`
  - Stores process IDs for tracking running services
  - Auto-generated, not committed to git

## Troubleshooting

### Port Already in Use

If you get errors about ports being in use:

1. Check what's using the port:
   
   **Linux/Mac:**
   ```bash
   lsof -i :34000  # Frontend port
   lsof -i :34001  # Backend port
   ```
   
   **Windows:**
   ```cmd
   netstat -ano | findstr :34000  REM Frontend port
   netstat -ano | findstr :34001  REM Backend port
   ```

2. Change the port in `.env` files:
   - Backend: Edit `backend\.env` and change `PORT=34001` to another port
   - Frontend: Edit `frontend\.env.local` and change `PORT=34000` to another port
   - Update `NEXT_PUBLIC_API_URL` in `frontend\.env.local` if backend port changed
   - Update `FRONTEND_URL` in `backend\.env` if frontend port changed

### Services Not Starting

1. Check the logs (stored in `logs/` directory):
   
   **Linux/Mac:**
   ```bash
   ./scripts/logs.sh        # Frontend logs (default)
   ./scripts/logs.sh -b     # Backend logs
   ```
   
   **Windows:**
   ```cmd
   scripts\win-logs.bat        REM Frontend logs (default)
   scripts\win-logs.bat -b     REM Backend logs
   ```

### UI Theme Settings

Lens supports multiple UI color themes (Warm, Purple, Blue, Green).

- Source/dev installs: open **Settings → General → Color Theme**
- The selection is stored in the browser (localStorage), so it persists per user/device

2. Verify dependencies are installed:
   
   **Linux/Mac:**
   ```bash
   cd backend && source venv/bin/activate && pip list
   cd frontend && npm list --depth=0
   ```
   
   **Windows:**
   ```cmd
   cd backend && call venv\Scripts\activate.bat && pip list
   cd frontend && npm list --depth=0
   ```

3. Check if services are actually running:
   
   **Linux/Mac:**
   ```bash
   ./scripts/status.sh
   ps aux | grep -E "(uvicorn|next dev)"
   ```
   
   **Windows:**
   ```cmd
   scripts\win-status.bat
   tasklist | findstr "python.exe node.exe"
   ```

## Platform-Specific Notes

### Linux/Mac
- Scripts use bash shell (`.sh` extension)
- Process management uses `kill` command
- Virtual environment activation: `source venv/bin/activate`

### Windows
- Scripts use CMD batch files (`.bat` extension, `win-` prefix)
- No PowerShell execution policy configuration needed
- Process management uses `taskkill` command
- Virtual environment activation: `call venv\Scripts\activate.bat`
- Color output in status script may vary depending on CMD version

## General Notes

- The scripts track process IDs in `scripts\.pids`
- Logs are written to `logs\backend.log` and `logs\frontend.log`
- If services are already running, start scripts will exit with an error
- Services can be started/stopped independently if needed (manual process management)

## Script Reference

| Function | Linux/Mac | Windows |
|----------|-----------|---------|
| Setup | `./scripts/setup.sh` | `scripts\win-setup.bat` |
| Start (Dev) | `./scripts/start.sh` | `scripts\win-start.bat` |
| Start (Prod) | `./scripts/start.sh -p` | `scripts\win-start.bat -p` |
| Stop | `./scripts/stop.sh` | `scripts\win-stop.bat` |
| Status | `./scripts/status.sh` | `scripts\win-status.bat` |
| Logs (Frontend) | `./scripts/logs.sh` | `scripts\win-logs.bat` |
| Logs (Backend) | `./scripts/logs.sh -b` | `scripts\win-logs.bat -b` |
| Test AI Key | `./scripts/test-ai-key.sh` | `scripts\win-test-ai-key.bat` |
| Version | `./scripts/version.sh` | `scripts\win-version.bat` |
