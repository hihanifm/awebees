# Windows Setup Guide

This guide explains how to set up Lens on Windows, including automatic installation of prerequisites.

## Quick Start

1. **Clone the repository:**
   ```cmd
   git clone <repository-url>
   cd awebees
   ```

2. **Run the setup script:**
   ```cmd
   scripts\win-setup.bat
   ```

## Alternative: Using Git Bash (Recommended)

If you have **Git Bash** installed (comes with Git for Windows), you can use the Linux/Mac shell scripts instead of the Windows batch scripts. The shell scripts now automatically detect Windows and use the correct paths.

### Why Use Git Bash?

- ✅ More reliable than batch scripts
- ✅ Better error handling
- ✅ Same scripts work on Linux, Mac, and Windows
- ✅ Better support for complex commands

### Setup with Git Bash

1. **Open Git Bash** (right-click in the project folder → "Git Bash Here")

2. **Run the setup script:**
   ```bash
   ./scripts/setup.sh
   ```

3. **Start the services:**
   ```bash
   # Development mode (default)
   ./scripts/start.sh
   
   # Production mode
   ./scripts/start.sh -p
   ```

4. **Check status:**
   ```bash
   ./scripts/status.sh
   ```

5. **Stop services:**
   ```bash
   ./scripts/stop.sh
   ```

The scripts automatically detect Windows and use `venv/Scripts/activate` instead of `venv/bin/activate`.

## Automatic Installation

The `win-setup.bat` script now includes **automatic installation** for Python and Node.js!

### How It Works

When you run `scripts\win-setup.bat`, the script will:

1. **Check for Node.js/npm**
   - If not found, it will ask: "Would you like to install Node.js automatically? [Y/N]"
   - If you answer **Y**, it will use `winget` to install Node.js LTS
   - Installation is silent and takes 2-5 minutes

2. **Check for Python**
   - If not found, it will ask: "Would you like to install Python automatically? [Y/N]"
   - If you answer **Y**, it will use `winget` to install Python 3.12
   - Installation is silent and takes 2-5 minutes

3. **After installation**
   - You'll be prompted to **restart your command prompt**
   - Run the setup script again to complete the setup

### Requirements for Automatic Installation

- **Windows 10 (version 1809 or later)** or **Windows 11**
- `winget` (Windows Package Manager) - comes pre-installed with modern Windows
- Internet connection

### Example Output

```cmd
C:\Users\YourName\awebees> scripts\win-setup.bat

Setting up Lens...

=== Checking Node.js Installation ===
Node.js/npm is not installed or not in PATH

Would you like to install Node.js automatically? [Y/N]
Enter choice: Y

Installing Node.js using winget...
This may take a few minutes...

Found Node.js LTS [OpenJS.NodeJS.LTS] Version 20.11.0
Installing...
Successfully installed

Node.js has been installed successfully!

IMPORTANT: You need to restart your command prompt for the changes to take effect.
After restarting, run this setup script again: scripts\win-setup.bat

Press any key to continue . . .
```

After restarting:

```cmd
C:\Users\YourName\awebees> scripts\win-setup.bat

Setting up Lens...

=== Checking Node.js Installation ===
Node.js v20.11.0 detected
npm 10.2.4 detected

=== Checking Python Installation ===
Python 3.12.1 detected

=== Backend Setup ===
Creating Python virtual environment...
Virtual environment created in backend\venv
Installing Python dependencies...
Python dependencies installed
Created backend\.env from .env.example

=== Frontend Setup ===
Installing Node.js dependencies...
Node.js dependencies installed
Created frontend\.env.local from .env.example

=== Setup Complete ===

You can now start the services with:
  scripts\win-start.bat

Or check status with:
  scripts\win-status.bat

Press any key to continue . . .
```

## Manual Installation

If automatic installation doesn't work or you prefer manual installation:

### Install Node.js Manually

1. Download from: https://nodejs.org/
2. Install the **LTS version** (recommended)
3. Make sure to check **"Add to PATH"** during installation
4. Restart your command prompt
5. Verify: `node --version` and `npm --version`

### Install Python Manually

1. Download from: https://www.python.org/downloads/
2. Install **Python 3.9 or later** (Python 3.12 recommended)
3. **IMPORTANT:** Check **"Add Python to PATH"** during installation
4. Restart your command prompt
5. Verify: `python --version`

### Then run setup

```cmd
scripts\win-setup.bat
```

## Troubleshooting

### "winget is not available on this system"

**Solution:** Update Windows to the latest version, or install App Installer from Microsoft Store.

**Alternative:** Install Python and Node.js manually (see above).

### "npm is not recognized" after installation

**Solution:** Restart your command prompt (or terminal) completely.

**Why:** Windows PATH environment variable updates require a new terminal session.

### Script hangs during installation

**Solution:** Check your internet connection. `winget` needs to download packages.

**Alternative:** Press `Ctrl+C` to cancel, then install manually.

### "Failed to create Python virtual environment"

**Solution:** 
1. Ensure Python is in PATH: `python --version`
2. Try: `python -m venv test_venv` in a test directory
3. If that fails, reinstall Python with "Add to PATH" checked

### Permission errors

**Solution:** Run Command Prompt as Administrator (Right-click → "Run as administrator").

## Next Steps

After setup completes successfully:

1. **Start the application:**
   ```cmd
   scripts\win-start.bat
   ```

2. **Access the application:**
   - Open browser to: http://localhost:34000 (development)
   - Or: http://localhost:34001 (production mode)

> Note: If `.env.example` files are missing, `scripts\\win-setup.bat` will generate basic defaults using ports **34000/34001**.

## Using the Windows ZIP Packages (No Git Needed)

If you downloaded a prebuilt ZIP from GitHub (for example `dist/windows/lens-package-with-python-4.0.0.zip`):

1. Extract the ZIP anywhere (e.g. `C:\\Users\\You\\Downloads\\Lens\\`)
2. Open the extracted folder (it contains `lens-start.bat`, `lens-stop.bat`, etc.)
3. Double-click `lens-start.bat` (or run it from Command Prompt)

**Variants:**
- **with-python**: includes an embedded Python runtime (recommended for easiest setup)
- **requires-python**: requires Python 3.x installed and available in PATH

**Playground:**
- After starting, open `http://127.0.0.1:34001/playground`

**Ports:**
- The app runs on **http://127.0.0.1:34001** by default (API + UI served by backend in packaged builds)
- If you add `backend\\.env` with `PORT=...`, the launcher will use it

3. **Check status:**
   ```cmd
   scripts\win-status.bat
   ```

4. **View logs:**
   ```cmd
   scripts\win-logs.bat        REM Frontend logs
   scripts\win-logs.bat -b     REM Backend logs
   ```

5. **Stop services:**
   ```cmd
   scripts\win-stop.bat
   ```

## UI Theme Settings

Lens supports multiple UI color themes (Warm, Purple, Blue, Green).

- Open **Settings → General → Color Theme**
- The selection is stored in the browser (localStorage), so it persists per user/device

## Support

- **Documentation:** See `/README.md` for full documentation
- **Scripts guide:** See `/scripts/README.md` for detailed script usage
- **Issues:** Check the issue tracker on GitHub

