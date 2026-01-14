# Windows Package Build System

This directory contains scripts and configuration for building Windows production packages for LensAI.

## Overview

The build system creates a single Windows installer that automatically installs Python and ripgrep via winget if needed:

1. **Windows Installer** - Auto-installs Python 3.12 and ripgrep via winget if not already installed (~50-100MB)

## Build Process

### Step 1: Prepare Packages (Linux/Mac)

Run the build script to prepare packages:

```bash
./scripts/build/build-windows.sh
```

This will:
- Build the frontend (`npm run build`)
- Download embeddable Python (for self-contained variant)
- Create package structures
- Generate Windows launcher scripts
- Create ZIP archives in `dist/windows/`

Output:
- `dist/windows/lens-package-requires-python-{version}.zip`

### Step 2: Create Installers (GitHub Actions)

Push the packages to GitHub and trigger the workflow:

```bash
# Commit and push packages
git add dist/windows/*.zip
git commit -m "Prepare Windows packages for v{version}"
git push

# Option 1: Manual trigger
gh workflow run build-windows-installer.yml

# Option 2: Create release tag (auto-triggers)
git tag v{version}
git push origin v{version}
```

The GitHub Actions workflow will:
- Extract the prepared packages
- Compile NSIS installer scripts
- Create `.exe` installers
- Upload as artifacts or attach to release

## Files

- `build/build-windows.sh` - Main build script (cross-platform shell script, works on Linux/Mac/Windows via Git Bash/WSL)
- `build/common/prepare-package.sh` - Package preparation script
- `build/common/verify-package.sh` - Package verification script
- `package/lens-start.bat` - Application launcher (included in Windows package)
- `package/lens-stop.bat` - Stop application script (included in Windows package)
- `package/lens-status.bat` - Status check script (included in Windows package)
- `package/lens-logs.bat` - View backend logs (included in Windows package)
- `installer.nsi` - NSIS script for installer (auto-installs Python and ripgrep via winget)
- `build-config.json` - Build configuration

## Configuration

Edit `build-config.json` to customize:
- App name and publisher
- Default installation directory
- Python version to bundle
- Shortcut options

## Prerequisites

**For local build (Linux/Mac):**
- Node.js and npm
- Python 3.x
- zip/unzip
- curl/wget

**For GitHub Actions:**
- NSIS (installed automatically by workflow)
- Windows runner (provided by GitHub)

## Testing

1. Test local build script
2. Test package structure
3. Test GitHub Actions workflow
4. Test installers on Windows VM
5. Verify application starts correctly
6. Test uninstaller

## Logs

Backend logs are written to:
```
{Installation Directory}\logs\backend.log
```

For example, if installed to `C:\Program Files (x86)\LensAI`:
```
C:\Program Files (x86)\LensAI\logs\backend.log
```

**View logs:**
- Run `lens-logs.bat` to view the last 20 lines
- Or open the log file directly in a text editor
- For real-time logs, use PowerShell:
  ```powershell
  Get-Content "C:\Program Files (x86)\LensAI\logs\backend.log" -Wait -Tail 20
  ```

## Troubleshooting

**Build fails:**
- Check prerequisites are installed
- Verify frontend builds successfully
- Check network connection (for Python download)

**GitHub Actions fails:**
- Ensure packages are committed to repository
- Check NSIS script syntax
- Verify version format matches VERSION file

**Installer doesn't work:**
- Test on clean Windows VM
- Check Windows Event Viewer for errors
- Verify winget is available (Windows 10 1809+ or Windows 11)
- If winget is not available, Python must be installed manually

**Application won't start:**
- Check logs: `lens-logs.bat` or `logs\backend.log`
- Verify Python is installed (installer should auto-install via winget)
- Check if the backend port is already in use (default: 34001, or `PORT` from `backend\.env`)
- Run `lens-status.bat` to check if backend is running

