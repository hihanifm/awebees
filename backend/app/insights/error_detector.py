"""Insight to detect errors in log files - Config-based implementation."""

INSIGHT_CONFIG = {
    "metadata": {
        "name": "Error Detector",
        "description": "Detects ERROR and FATAL log lines in log files"
    },
    "filters": {
        "line_pattern": r"\b(ERROR|FATAL)\b"
    }
}
