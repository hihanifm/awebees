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

### Built-in Samples (This Directory)

To add additional sample files to the built-in samples:

1. Place the compressed file (`.zip` or `.gz`) in this directory
2. Update `backend/app/core/constants.py` to add the sample to `SAMPLE_FILES` dictionary
3. Update this README with documentation

### External Samples (LensInsights)

You can also add sample files to external insight directories (e.g., LensInsights):

1. Create a `samples/` subdirectory in your external insight directory
2. Place sample files (`.txt`, `.log`, `.zip`, `.gz`) in the `samples/` directory
3. Optionally create metadata JSON files (e.g., `my-sample.json`) with:
   ```json
   {
     "name": "My Sample",
     "description": "Description of the sample",
     "size_mb": 5.2,
     "recommended_insights": ["error_detector", "line_count"]
   }
   ```
4. Lens will automatically discover and extract samples from all configured insight paths

External samples are automatically discovered and appear in the Lens UI alongside built-in samples. Users can select from multiple samples using a dropdown selector.

## Notes

- Sample files are automatically extracted on server startup
- Extraction only happens once (skipped if `.txt` already exists)
- Keep compressed versions in git, ignore extracted versions
- Large files (>50MB uncompressed) should be stored compressed
- Samples from external insight paths are automatically discovered and available in the UI

