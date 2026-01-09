# LensAI

A modular engine for extracting insights from messy data!

A local web application for analyzing log files with a plugin-based insight system.

![Lens Main Interface](lens_1.png)
*Main interface showing file selection, available insights, and real-time analysis progress*

## Architecture

- **Frontend**: Next.js App Router + TypeScript + shadcn/ui + Tailwind CSS (Port 34000)
- **Backend**: FastAPI + Python (Port 34001)

## Quick Start

### Prerequisites

- Python 3.x
- Node.js and npm
- Git

**Note for Windows users:** The `win-setup.bat` script can automatically install Python and Node.js using `winget` if they're not already installed. Just run the setup script and follow the prompts. See the [Windows Setup Guide](WINDOWS-SETUP-GUIDE.md) for detailed instructions and troubleshooting.

### Setup (Linux/Mac)

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
   ./scripts/start.sh        # Development mode (default)
   ./scripts/start.sh -p     # Production mode (builds frontend automatically)
   ```
   
   **Production Mode:**
   - Automatically builds the frontend and serves it from the backend
   - Single server on port 34001 (API + Frontend)
   - No separate frontend server needed
   
   **Development Mode:**
   - Separate servers: Frontend (34000) and Backend (34001)
   - Hot reload enabled for better development experience

4. Check Status:
   ```bash
   ./scripts/status.sh
   ```

5. View Logs:
   ```bash
   ./scripts/logs.sh        # Frontend logs (default)
   ./scripts/logs.sh -b     # Backend logs
   ```

6. Stop Services:
   ```bash
   ./scripts/stop.sh
   ```

### Setup (Windows)

> 📖 **Detailed Guide:** See [WINDOWS-SETUP-GUIDE.md](WINDOWS-SETUP-GUIDE.md) for comprehensive setup instructions and troubleshooting.

1. Clone the repository:
   ```cmd
   git clone <repository-url>
   cd awebees
   ```

2. Run setup script (one-time setup):
   ```cmd
   scripts\win-setup.bat
   ```
   
   This will:
   - **Automatically detect and offer to install Python and Node.js if not found**
   - Uses `winget` (Windows Package Manager) for automatic installation
   - Create Python virtual environment
   - Install all dependencies (Python and Node.js)
   - Create `.env` files from examples
   
   **Note:** If Python or Node.js are installed during setup, you'll need to restart your command prompt and run the setup script again.

3. Start Services:
   ```cmd
   scripts\win-start.bat        REM Development mode (default)
   scripts\win-start.bat -p     REM Production mode (builds frontend automatically)
   ```
   
   **Production Mode:**
   - Automatically builds the frontend and serves it from the backend
   - Single server on port 34001 (API + Frontend)
   - No separate frontend server needed
   
   **Development Mode:**
   - Separate servers: Frontend (34000) and Backend (34001)
   - Hot reload enabled for better development experience

4. Check Status:
   ```cmd
   scripts\win-status.bat
   ```

5. View Logs:
   ```cmd
   scripts\win-logs.bat        REM Frontend logs (default)
   scripts\win-logs.bat -b     REM Backend logs
   ```

6. Stop Services:
   ```cmd
   scripts\win-stop.bat
   ```

**Note:** Windows scripts use CMD batch files (no PowerShell execution policy configuration needed).

## Configuration

### Environment Variables

Both frontend and backend use environment variables for configuration:

- **Backend**: See `backend/.env.example` - Copy to `backend/.env`
- **Frontend**: See `frontend/.env.example` - Copy to `frontend/.env.local`

Default ports:
- Frontend: 34000
- Backend: 34001

## Logs

Error and application logs are stored in the `logs/` directory:

- **Backend logs**: `logs/backend.log`
- **Frontend logs**: `logs/frontend.log`

View logs:

**Linux/Mac:**
```bash
./scripts/logs.sh        # Frontend logs (last 20 lines)
./scripts/logs.sh -b     # Backend logs (last 20 lines)
tail -f logs/backend.log   # Backend logs (follow mode)
tail -f logs/frontend.log  # Frontend logs (follow mode)
```

**Windows:**
```cmd
scripts\win-logs.bat        REM Frontend logs (last 20 lines)
scripts\win-logs.bat -b     REM Backend logs (last 20 lines)
```

## Features

LensAI provides a modular plugin-based system for analyzing log files:

### Available Insights

- **Line Count**: Counts total lines, empty lines, and non-empty lines in log files
- **Error Detector**: Detects ERROR and FATAL log lines in log files
- **Android Crash Detector**: Specialized Android crash analysis with AI-powered insights

### 🧪 Playground

The **Playground** is an interactive environment for experimenting with ripgrep filters and AI prompts in real-time. Perfect for:
- **Testing ripgrep patterns** with immediate feedback
- **Iterating on AI prompts** to refine analysis
- **Learning ripgrep syntax** with live examples
- **Developing custom analysis workflows**

**Access:** Click the flask icon (🧪) in the status bar, or navigate to `/playground`

📖 **[Read the Playground Guide →](PLAYGROUND.md)**

### Quick Start with Sample File

**New to LensAI?** Try it immediately with the included sample files:

1. Start the application (see Quick Start above)
2. A sample file is **automatically loaded** when the page opens
   - If multiple samples are available, use the **"Select Sample"** dropdown to choose a different one
   - Samples are discovered from built-in and external insight directories
3. Select one or more insights (try "Error Detector" or "Line Count")
4. Click **"Analyze Files"** and watch real-time progress

Sample files are automatically extracted on first startup. Perfect for testing performance and exploring insights!

**Command Line:**
```bash
# From backend directory
cd backend
python -m app.insights.error_detector samples/android-bugreport.txt
```

### Usage

1. **Enter File or Folder Paths**: 
   - Enter absolute paths to log files or folders on the server
   - Folders will be scanned recursively
   - The last used paths will be prefilled automatically
   - Example: `/Users/username/logs/file.log` or `/var/log/app.log`
   - **Tip:** A sample file is automatically loaded on startup—you can replace it with your own file path or use the "Select Sample" dropdown to choose a different sample

2. **Select Insights**: 
   - Choose one or more insights to run on your files
   - Insights are organized by category (e.g., "General")

3. **Analyze**: 
   - Click "Analyze Files" to start the analysis
   - View real-time progress and results
   - Cancel analysis mid-flight if needed

![Analysis Results with Statistics](lens_2.png)
*Analysis results showing performance statistics, crash details, and AI-powered analysis*

![Detailed AI Analysis](lens_3.png)
*AI analysis providing summary, common patterns, root causes, recommended fixes, and priority guidance*

### Status Indicators

The footer displays:
- **Version**: Current application version (e.g., v2.5.0)
- **Environment**: DEV or PROD
- **API Status**: Online/Offline
- **Profiling**: Indicates if backend profiling is enabled

## Development

**Development Mode:**
- Backend API docs: http://localhost:34001/docs
- Frontend: http://localhost:34000
- Version API: http://localhost:34001/api/version

**Production Mode:**
- Single server: http://localhost:34001 (serves both API and frontend)
- Backend API docs: http://localhost:34001/docs
- Frontend: http://localhost:34001

## Creating Custom Insights

LensAI supports two approaches for creating insights:

### Config-Based Insights (Recommended)

For most filtering use cases, use the simple declarative approach:

```python
"""My insight."""

INSIGHT_CONFIG = {
    "metadata": {
        "id": "my_insight",
        "name": "My Insight",
        "description": "Finds patterns"
    },
    "filters": {
        "line_pattern": r"\b(ERROR|WARNING)\b",
        "regex_flags": "IGNORECASE"
    }
}

# Optional: Custom post-processing
def process_results(filter_result):
    lines = filter_result.get_lines()
    return {
        "content": f"Found {len(lines)} matches",
        "metadata": {"total": len(lines)}
    }

if __name__ == "__main__":
    from app.utils.config_insight_runner import main_config_standalone
    main_config_standalone(__file__)
```

**Benefits:**
- 70% less code than class-based approach
- Declarative configuration
- Automatic progress tracking and cancellation
- Standalone execution support

### Class-Based Insights (Advanced)

For complex logic beyond filtering, use Python classes:

```python
from app.core.insight_base import Insight

class CustomInsight(Insight):
    # Full control over analysis logic
    async def analyze(self, file_paths, ...):
        # Your custom logic
        pass
```

**Complete Guide:** See [`backend/app/insights/README.md`](backend/app/insights/README.md) for detailed documentation, examples, and best practices.

**Examples:**
- [`error_detector.py`](backend/app/insights/error_detector.py) - Config-based with custom formatting
- [`line_count.py`](backend/app/insights/line_count.py) - Class-based with custom logic

## Version Management

The project uses a unified versioning system with a single source of truth.

### Version File

The version is stored in `VERSION` at the project root. This is the single source of truth for the application version.

### Version Script

Use the version management script to manage versions:

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

### Version Endpoint

The backend provides a version endpoint:
- **GET** `/api/version` - Returns the current application version

### Release Workflow

1. Update the version using the version script:
   
   **Linux/Mac:**
   ```bash
   ./scripts/version.sh bump patch    # or major/minor
   ```
   
   **Windows:**
   ```cmd
   scripts\win-version.bat bump patch    REM or major/minor
   ```

2. Update `CHANGELOG.md` with the changes for the new version

3. Commit the changes:
   ```bash
   git add VERSION CHANGELOG.md frontend/package.json
   git commit -m "Bump version to X.Y.Z"
   ```

4. Tag the release:
   
   **Linux/Mac:**
   ```bash
   git tag -a v$(./scripts/version.sh get) -m "Release v$(./scripts/version.sh get)"
   git push origin master
   git push origin --tags
   ```
   
   **Windows:**
   ```cmd
   for /f %i in ('scripts\win-version.bat get') do set VERSION=%i
   git tag -a v%VERSION% -m "Release v%VERSION%"
   git push origin master
   git push origin --tags
   ```

## Project Structure

```
awebees/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── scripts/          # Management scripts
├── logs/             # Application logs
├── VERSION           # Application version (single source of truth)
├── CHANGELOG.md      # Version history
└── .cursor/          # Cursor IDE rules
```

## Documentation

- **[Playground Guide](PLAYGROUND.md)** - Interactive ripgrep and AI experimentation environment
- **[AI Setup Guide](docs/AI_SETUP.md)** - Configure OpenAI API integration
- **[Windows Setup Guide](WINDOWS-SETUP-GUIDE.md)** - Windows-specific installation instructions
- **[Features](FEATURES.md)** - Detailed feature documentation
- **[Changelog](CHANGELOG.md)** - Version history and release notes

