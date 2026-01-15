INSIGHT_CONFIG = {
    "metadata": {
        "name": "Error Detector",
        "description": "Detects ERROR and FATAL log lines in log files",
        "author": "m.hanifa"
    },
    "file_filters": [
        {
            "file_patterns": [],
            "line_filters": [
                {
                    "ripgrep_command": r"\b(ERROR|FATAL)\b",
                    "reading_mode": "lines"
                }
            ]
        }
    ]
}
