"""HTTP request/response logging middleware for FastAPI."""

import json
import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)


class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        from app.core.config import AppConfig
        
        # Initialize AppConfig to load from config.json
        AppConfig._initialize()
        
        # Check if HTTP logging is enabled
        if not AppConfig.get_http_logging():
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Read request body if present (this consumes it, so we need to recreate it)
        # Only read body for methods that typically have bodies
        request_body = b""
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            request_body = await self._read_request_body(request)
            
            # Recreate request with body for downstream processing
            # Store original receive function
            original_receive = request._receive
            
            async def receive():
                if hasattr(request, '_body_read'):
                    # Body already read, return empty
                    return await original_receive()
                else:
                    # Return the body we read
                    request._body_read = True
                    return {"type": "http.request", "body": request_body}
            
            # Replace request's receive function
            request._receive = receive
        
        # Log request
        self._log_request(request, request_body)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # For streaming responses, we can't easily read the body
        # For regular responses, we can wrap it to capture the body
        if isinstance(response, StreamingResponse):
            # Log response without body for streaming responses
            self._log_response(request, response, None, duration, is_stream=True)
        else:
            # Wrap response to capture body
            response = await self._capture_response_body(request, response, duration)
        
        return response
    
    async def _read_request_body(self, request: Request) -> bytes:
        """Read request body."""
        body = b""
        async for chunk in request.stream():
            body += chunk
        return body
    
    async def _capture_response_body(self, request: Request, response: Response, duration: float) -> Response:
        """Capture response body for logging."""
        response_body = b""
        
        # Read response body
        async for chunk in response.body_iterator:
            response_body += chunk
        
        # Log response
        self._log_response(request, response, response_body, duration, is_stream=False)
        
        # Create new response with the body
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
    
    def _log_request(self, request: Request, body: bytes) -> None:
        """Log HTTP request details."""
        # Mask sensitive headers
        headers = dict(request.headers)
        masked_headers = self._mask_sensitive_headers(headers)
        
        # Parse body if possible
        body_str = self._format_body(body, request.headers.get("content-type", ""))
        
        logger.info("=" * 80)
        logger.info("HTTP Request")
        logger.info("=" * 80)
        logger.info(f"Method: {request.method}")
        logger.info(f"URL: {request.url}")
        logger.info(f"Path: {request.url.path}")
        logger.info(f"Query: {request.url.query}")
        logger.info(f"Headers: {json.dumps(masked_headers, indent=2)}")
        if body_str:
            logger.info(f"Body: {body_str}")
        logger.info("=" * 80)
    
    def _log_response(self, request: Request, response: Response, body: bytes, duration: float, is_stream: bool = False) -> None:
        """Log HTTP response details."""
        # Parse body if possible
        content_type = response.headers.get("content-type", "")
        body_str = None
        if body is not None:
            body_str = self._format_body(body, content_type)
        
        logger.info("=" * 80)
        logger.info("HTTP Response")
        logger.info("=" * 80)
        logger.info(f"Method: {request.method}")
        logger.info(f"URL: {request.url}")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Duration: {duration:.3f}s")
        logger.info(f"Headers: {json.dumps(dict(response.headers), indent=2)}")
        if is_stream:
            logger.info("Body: [Streaming response - body not captured]")
        elif body_str:
            logger.info(f"Body: {body_str}")
        logger.info("=" * 80)
    
    def _mask_sensitive_headers(self, headers: dict) -> dict:
        """Mask sensitive data in headers."""
        masked = headers.copy()
        sensitive_keys = ["authorization", "cookie", "x-api-key", "api-key"]
        for key in sensitive_keys:
            if key.lower() in [k.lower() for k in masked.keys()]:
                for header_key in list(masked.keys()):
                    if header_key.lower() == key.lower():
                        value = masked[header_key]
                        if key.lower() == "authorization" and value.startswith("Bearer "):
                            token = value[7:]
                            if len(token) > 8:
                                masked[header_key] = f"Bearer {token[:8]}...{token[-4:]}"
                            else:
                                masked[header_key] = "Bearer ***"
                        else:
                            masked[header_key] = "***"
        return masked
    
    def _format_body(self, body: bytes, content_type: str) -> str:
        """Format body for logging, truncating if too long."""
        if not body:
            return ""
        
        # Truncate very large bodies
        max_length = 5000
        if len(body) > max_length:
            truncated = body[:max_length]
            try:
                body_str = truncated.decode('utf-8', errors='ignore')
                return f"{body_str}... [truncated, total length: {len(body)} bytes]"
            except Exception:
                return f"[binary data, {len(body)} bytes, truncated]"
        
        # Try to decode as text
        try:
            body_str = body.decode('utf-8', errors='ignore')
            
            # Try to pretty-print JSON
            if "application/json" in content_type.lower():
                try:
                    json_obj = json.loads(body_str)
                    return json.dumps(json_obj, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    pass
            
            return body_str
        except Exception:
            return f"[binary data, {len(body)} bytes]"
