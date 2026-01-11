"""
Fast Error Detector using ripgrep for ultra-fast pattern matching.
Demonstrates 10-100x speed improvement over Python regex on large files.

This insight is functionally identical to error_detector.py but uses ripgrep
for significantly faster performance on large log files.
"""

INSIGHT_CONFIG = {
    "metadata": {
        "name": "Fast Error Detector (ripgrep)",
        "description": "Ultra-fast ERROR/FATAL detection using ripgrep - 10-100x faster than Python regex"
    },
    "file_filters": [
        {
            "file_patterns": [r"dumpstate-", r"bugreport-", r"dumpstate.txt"],
            "line_filters": [
                {
                    "pattern": r"\b(ERROR|FATAL)\b",
                    "reading_mode": "ripgrep"
                }
            ]
        }
    ]
}
