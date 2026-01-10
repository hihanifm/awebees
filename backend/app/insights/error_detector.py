"""Insight to detect errors in log files - Config-based implementation."""

INSIGHT_CONFIG = {
    "metadata": {
        "name": "Error Detector",
        "description": "Detects ERROR and FATAL log lines in log files"
    },
    "file_filters": [
        {
            "id": "all_files",
            "file_patterns": [],  # Empty means process all files
            "line_filters": [
                {
                    "id": "errors",
                    "pattern": r"\b(ERROR|FATAL)\b"
                }
            ]
        }
    ]
}
