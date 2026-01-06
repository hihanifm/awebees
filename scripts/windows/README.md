# Windows Package Build System

This directory contains scripts and configuration for building Windows production packages for Lens.

## Overview

The build system creates two Windows installer variants:

1. **Self-contained installer** - Bundles Python runtime (~150-200MB)
2. **Python-required installer** - Requires Python 3.x pre-installed (~50-100MB)

## Build Process

### Step 1: Prepare Packages (Linux/Mac)

Run the build script to prepare packages:

```bash
./scripts/build-windows.sh
```

This will:
- Build the frontend (`npm run build`)
- Download embeddable Python (for self-contained variant)
- Create package structures
- Generate Windows launcher scripts
- Create ZIP archives in `dist/windows/`

Output:
- `dist/windows/lens-package-with-python-{version}.zip`
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

- `build-windows.sh` - Main build script (runs on Linux/Mac)
- `prepare-package.sh` - Package preparation script
- `lens-start.bat` - Application launcher (Windows)
- `lens-stop.bat` - Stop application script (Windows)
- `lens-status.bat` - Status check script (Windows)
- `lens-logs.bat` - View backend logs (Windows)
- `installer-with-python.nsi` - NSIS script for self-contained installer
- `installer-requires-python.nsi` - NSIS script for Python-required installer
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

For example, if installed to `C:\Program Files (x86)\Lens`:
```
C:\Program Files (x86)\Lens\logs\backend.log
```

**View logs:**
- Run `lens-logs.bat` to view the last 20 lines
- Or open the log file directly in a text editor
- For real-time logs, use PowerShell:
  ```powershell
  Get-Content "C:\Program Files (x86)\Lens\logs\backend.log" -Wait -Tail 20
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
- Verify Python installation (for requires-python variant)

**Application won't start:**
- Check logs: `lens-logs.bat` or `logs\backend.log`
- Verify Python is installed (for requires-python variant)
- Check if port 34001 is already in use
- Run `lens-status.bat` to check if backend is running

