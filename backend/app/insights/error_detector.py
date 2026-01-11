"""Insight to detect errors in log files - Config-based implementation."""

INSIGHT_CONFIG = {
    "metadata": {
        "name": "Error Detector",
        "description": "Detects ERROR and FATAL log lines in log files"
    },
    "file_filters": [
        {
            "file_patterns": [],
            "line_filters": [
                {
                    "pattern": r"\b(ERROR|FATAL)\b"
                }
            ]
        }
    ]
}
