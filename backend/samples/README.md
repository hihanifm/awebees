# Sample Files

This directory contains sample log files that users can use to quickly test Lens insights without needing their own files.

## Available Samples

### Android Bugreport

**File:** `android-bugreport.txt` (57MB, auto-extracted from `android-bugreport.zip`)

A comprehensive Android bugreport from an emulator, containing:
- System logs with various severity levels (INFO, DEBUG, WARNING, ERROR, FATAL)
- Application logs and crash information
- System state and performance metrics
- Network and connectivity information
- Hardware and sensor data

**Perfect for testing:**
- Error Detector insight (finds ERROR and FATAL lines)
- Line Count insight (tests performance with large files)
- Custom insights that filter log patterns

## Usage

### Via Web UI

1. Start the Lens application
2. Click "Load Sample File" button on the main page
3. The sample file path will be pre-filled
4. Select insights and click "Analyze Files"

### Via Command Line

```bash
# From backend directory
cd backend

# Test error detector
python -m app.insights.error_detector samples/android-bugreport.txt

# Test line count
python -m app.insights.line_count samples/android-bugreport.txt

# With verbose output
python -m app.insights.error_detector samples/android-bugreport.txt --verbose
```

### Via Test Runner Script

```bash
# From project root
./scripts/run_insight.py error_detector backend/samples/android-bugreport.txt
```

## Auto-Extraction

The sample file is stored as a compressed ZIP (5.5MB) to save repository space. On first server startup, it's automatically extracted to `android-bugreport.txt` (57MB).

The extracted `.txt` file is gitignored and only exists locally after extraction.

## File Details

- **Source:** Android Emulator bugreport
- **Size (compressed):** 5.5MB
- **Size (uncompressed):** 57MB
- **Format:** Plain text log file
- **Generated:** 2026-01-06
- **Device:** Android SDK Emulator (arm64)

## Adding More Samples

To add additional sample files:

1. Place the compressed file (`.zip` or `.gz`) in this directory
2. Update `backend/app/main.py` startup event to extract it
3. Update this README with documentation
4. Add the path to `backend/app/core/constants.py`
5. Update the frontend UI if needed

## Notes

- Sample files are automatically extracted on server startup
- Extraction only happens once (skipped if `.txt` already exists)
- Keep compressed versions in git, ignore extracted versions
- Large files (>50MB uncompressed) should be stored compressed

