from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import logging
import html
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logs", tags=["logs"])


def get_project_root() -> Path:
    """Get the project root directory."""
    # backend/app/api/routes/logs.py -> backend/app/api/routes -> backend/app/api -> backend/app -> backend
    current_file = Path(__file__)
    return current_file.parent.parent.parent.parent.parent


def get_last_n_lines(file_path: Path, n: int = 500) -> list[str]:
    """Read the last N lines from a file efficiently."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # Return last N lines
            return lines[-n:] if len(lines) > n else lines
    except Exception as e:
        logger.error(f"Error reading log file {file_path}: {e}", exc_info=True)
        raise


def format_log_as_html(log_type: str, lines: list[str]) -> str:
    """Format log lines as HTML page."""
    content = '\n'.join(lines)
    # Escape HTML special characters
    content = html.escape(content)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{log_type} Log - LensAI</title>
    <style>
        body {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
            font-size: 13px;
            line-height: 1.5;
            margin: 0;
            padding: 20px;
            background-color: #1e1e1e;
            color: #d4d4d4;
        }}
        .header {{
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #3e3e3e;
        }}
        .header h1 {{
            margin: 0;
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
        }}
        .header p {{
            margin: 5px 0 0 0;
            font-size: 12px;
            color: #858585;
        }}
        pre {{
            margin: 0;
            padding: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            background: transparent;
        }}
        .log-content {{
            background-color: #252526;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #3e3e3e;
            max-height: calc(100vh - 120px);
            overflow-y: auto;
        }}
        @media (prefers-color-scheme: light) {{
            body {{
                background-color: #ffffff;
                color: #1e1e1e;
            }}
            .header {{
                border-bottom-color: #e1e1e1;
            }}
            .header h1 {{
                color: #000000;
            }}
            .header p {{
                color: #666666;
            }}
            .log-content {{
                background-color: #f8f8f8;
                border-color: #e1e1e1;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{log_type} Log</h1>
        <p>Last 500 lines | LensAI</p>
    </div>
    <div class="log-content">
        <pre>{content}</pre>
    </div>
    </body>
</html>"""
    return html_content


@router.get("/backend", response_class=HTMLResponse)
async def get_backend_log():
    """Get the last 500 lines of the backend log file."""
    try:
        project_root = get_project_root()
        log_path = project_root / "logs" / "backend.log"
        
        logger.info(f"Logs API: Reading backend log from: {log_path}")
        
        if not log_path.exists():
            logger.warning(f"Logs API: Backend log file not found at: {log_path}")
            error_html = format_log_as_html(
                "Backend Log",
                [f"Log file not found: {log_path}"]
            )
            return HTMLResponse(content=error_html, status_code=404)
        
        lines = get_last_n_lines(log_path, n=500)
        logger.info(f"Logs API: Successfully read {len(lines)} lines from backend log")
        
        html_content = format_log_as_html("Backend Log", lines)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Logs API: Error reading backend log: {e}", exc_info=True)
        error_html = format_log_as_html(
            "Backend Log",
            [f"Error reading log file: {str(e)}"]
        )
        return HTMLResponse(content=error_html, status_code=500)


@router.get("/frontend", response_class=HTMLResponse)
async def get_frontend_log():
    """Get the last 500 lines of the frontend log file."""
    try:
        project_root = get_project_root()
        log_path = project_root / "logs" / "frontend.log"
        
        logger.info(f"Logs API: Reading frontend log from: {log_path}")
        
        if not log_path.exists():
            logger.warning(f"Logs API: Frontend log file not found at: {log_path}")
            error_html = format_log_as_html(
                "Frontend Log",
                [f"Log file not found: {log_path}"]
            )
            return HTMLResponse(content=error_html, status_code=404)
        
        lines = get_last_n_lines(log_path, n=500)
        logger.info(f"Logs API: Successfully read {len(lines)} lines from frontend log")
        
        html_content = format_log_as_html("Frontend Log", lines)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Logs API: Error reading frontend log: {e}", exc_info=True)
        error_html = format_log_as_html(
            "Frontend Log",
            [f"Error reading log file: {str(e)}"]
        )
        return HTMLResponse(content=error_html, status_code=500)
