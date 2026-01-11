from pathlib import Path

# Get project paths
# backend/app/core/constants.py -> backend/app/core -> backend/app -> backend
BACKEND_DIR = Path(__file__).parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent           # backend -> project root
SAMPLES_DIR = BACKEND_DIR / "samples"

# Sample file paths
SAMPLE_ANDROID_BUGREPORT = str(SAMPLES_DIR / "android-bugreport.txt")

# Sample files dictionary for easy reference
SAMPLE_FILES = {
    "android_bugreport": {
        "path": SAMPLE_ANDROID_BUGREPORT,
        "name": "Android Bugreport",
        "description": "Comprehensive Android system log (57MB)",
        "size_mb": 57,
        "recommended_insights": ["error_detector", "line_count"]
    }
}


def get_built_in_samples_dir() -> Path:
    return SAMPLES_DIR

