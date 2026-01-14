import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncIterator
import httpx

logger = logging.getLogger(__name__)


class AIService:
    """
    Stateless AI service that reads configuration directly from AIConfig.
    No instance variables - all config values are read from AIConfig on each use.
    """
    
    def __init__(self):
        # Empty - AIService is stateless and reads directly from AIConfig
        pass
    
    def _get_base_url(self) -> str:
        """Get base URL from AIConfig."""
        from app.core.config import AIConfig
        return AIConfig.BASE_URL
    
    def _get_api_key(self) -> str:
        """Get API key from AIConfig."""
        from app.core.config import AIConfig
        return AIConfig.API_KEY or ""
    
    def _get_model(self) -> str:
        """Get model from AIConfig, with default fallback."""
        from app.core.config import AIConfig
        model = AIConfig.MODEL.strip() if AIConfig.MODEL else "gpt-4o-mini"
        return model if model else "gpt-4o-mini"
    
    def _get_max_tokens(self) -> int:
        """Get max_tokens from AIConfig."""
        from app.core.config import AIConfig
        return AIConfig.MAX_TOKENS
    
    def _get_temperature(self) -> float:
        """Get temperature from AIConfig."""
        from app.core.config import AIConfig
        return AIConfig.TEMPERATURE
    
    def _get_timeout(self) -> int:
        """Get timeout from AIConfig."""
        from app.core.config import AIConfig
        return AIConfig.TIMEOUT
    
    def _is_detailed_logging_enabled(self) -> bool:
        """Check if detailed logging is enabled via config."""
        try:
            from app.core.config import AIConfig
            return AIConfig.DETAILED_LOGGING
        except Exception:
            return False
    
    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive data in headers for logging."""
        masked = headers.copy()
        if "Authorization" in masked:
            # Mask API key but keep Bearer prefix visible
            auth = masked["Authorization"]
            if auth.startswith("Bearer "):
                key = auth[7:]
                if len(key) > 8:
                    masked["Authorization"] = f"Bearer {key[:8]}...{key[-4:]}"
                else:
                    masked["Authorization"] = "Bearer ***"
        return masked
    
    def _log_detailed_request(self, method: str, url: str, headers: Dict[str, str], payload: Optional[Dict[str, Any]] = None) -> None:
        """Log detailed HTTP request information."""
        if not self._is_detailed_logging_enabled():
            return
        
        masked_headers = self._mask_sensitive_headers(headers)
        
        logger.info("=" * 80)
        logger.info("AI Service: Detailed Request Log")
        logger.info("=" * 80)
        logger.info(f"Method: {method}")
        logger.info(f"URL: {url}")
        logger.info(f"Headers: {json.dumps(masked_headers, indent=2)}")
        
        if payload:
            # Create a copy for logging to avoid modifying original
            log_payload = payload.copy()
            
            # Truncate very long content in messages for readability
            if "messages" in log_payload:
                truncated_messages = []
                for msg in log_payload["messages"]:
                    msg_copy = msg.copy()
                    if "content" in msg_copy and len(msg_copy["content"]) > 500:
                        msg_copy["content"] = msg_copy["content"][:500] + f"... [truncated, total length: {len(msg['content'])} chars]"
                    truncated_messages.append(msg_copy)
                log_payload["messages"] = truncated_messages
            
            logger.info(f"Payload: {json.dumps(log_payload, indent=2, ensure_ascii=False)}")
        logger.info("=" * 80)
    
    def _log_detailed_response(self, status_code: int, headers: Dict[str, str], body: Optional[str] = None, is_stream: bool = False) -> None:
        """Log detailed HTTP response information."""
        if not self._is_detailed_logging_enabled():
            return
        
        logger.info("=" * 80)
        logger.info("AI Service: Detailed Response Log")
        logger.info("=" * 80)
        logger.info(f"Status Code: {status_code}")
        logger.info(f"Headers: {json.dumps(dict(headers), indent=2)}")
        
        if body:
            # Truncate very long response bodies
            if len(body) > 1000:
                logger.info(f"Body: {body[:1000]}... [truncated, total length: {len(body)} chars]")
            else:
                logger.info(f"Body: {body}")
        elif is_stream:
            logger.info("Body: [Streaming response - body logged as chunks arrive]")
        
        logger.info("=" * 80)
    
    def get_system_prompt(self, prompt_type: str) -> str:
        prompts = {
            "summarize": """You are a log analysis assistant. Summarize the following log analysis results concisely.
Focus on:
- Key findings
- Important patterns
- Critical issues

Be brief and actionable.""",
            
            "explain": """You are a log analysis expert. Analyze the following log data and explain:
- What patterns you observe
- What these patterns indicate
- Potential root causes
- System behavior insights

Be thorough but concise.""",
            
            "recommend": """You are a system reliability expert. Based on the following log analysis, provide:
- Actionable recommendations
- Priority of actions
- Potential risks to address
- Best practices to follow

Be specific and practical."""
        }
        return prompts.get(prompt_type, prompts["explain"])
    
    def build_prompt(
        self,
        content: str,
        prompt_type: str = "explain",
        custom_prompt: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build the user prompt with optional variable substitution.
        
        Args:
            content: The content to analyze
            prompt_type: Type of analysis (summarize, explain, recommend, custom)
            custom_prompt: Custom prompt template (if prompt_type is "custom")
            variables: Variables to substitute in custom prompt
        
        Returns:
            Complete prompt string
        """
        if prompt_type == "custom" and custom_prompt:
            prompt = custom_prompt
            
            if variables:
                for key, value in variables.items():
                    placeholder = "{" + key + "}"
                    if placeholder in prompt:
                        prompt = prompt.replace(placeholder, str(value))
            
            if "{result_content}" not in custom_prompt:
                prompt += f"\n\n{content}"
            else:
                prompt = prompt.replace("{result_content}", content)
        else:
            prompt = content
        
        return prompt
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL with /v1 automatically added if not present.
        
        Args:
            endpoint: The API endpoint path (e.g., "/chat/completions", "/models")
        
        Returns:
            Full URL with /v1 prefix if needed
        """
        base_url = self._get_base_url()
        # Strip trailing slashes
        base_url = base_url.rstrip('/')
        
        # Check if /v1 is already in the base URL (case-insensitive)
        base_url_lower = base_url.lower()
        if not base_url_lower.endswith('/v1'):
            # Add /v1 if not present
            base_url = f"{base_url}/v1"
        
        # Ensure endpoint starts with /
        if not endpoint.startswith('/'):
            endpoint = f"/{endpoint}"
        
        return f"{base_url}{endpoint}"
    
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for AI API requests."""
        api_key = self._get_api_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Internal-Request": "true"  # Dummy header - customize as needed
        }
        
        # Optional: Add custom headers from config if needed
        # custom_headers = os.getenv("OPENAI_CUSTOM_HEADERS", "{}")
        # if custom_headers:
        #     try:
        #         headers.update(json.loads(custom_headers))
        #     except:
        #         pass
        
        return headers
    
    async def analyze_stream(
        self,
        content: str,
        prompt_type: str = "explain",
        custom_prompt: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Analyze content with AI and stream the response.
        
        Args:
            content: Content to analyze
            prompt_type: Type of analysis
            custom_prompt: Custom prompt template
            variables: Variables for prompt substitution
            
        Yields:
            Chunks of the AI response as they arrive
            
        Raises:
            Exception: If AI service is not configured or request fails
        """
        from app.core.config import AIConfig
        if not AIConfig.is_configured():
            raise ValueError("AI service is not configured. Please set OPENAI_API_KEY and enable AI_ENABLED.")
        
        system_prompt = self.get_system_prompt(prompt_type)
        user_prompt = self.build_prompt(content, prompt_type, custom_prompt, variables)
        
        # Get config values from AIConfig
        base_url = self._get_base_url()
        model = self._get_model()
        max_tokens = self._get_max_tokens()
        temperature = self._get_temperature()
        timeout = self._get_timeout()
        
        logger.info(f"AI Service: Starting streaming analysis (model: {model}, prompt_type: {prompt_type})")
        
        url = self._build_url("/chat/completions")
        headers = self._build_headers()
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        # Log detailed request if enabled
        self._log_detailed_request("POST", url, headers, payload)
        
        # Log request details (truncate content for readability)
        logger.info(f"AI Service: Sending request to {url}")
        logger.debug(f"AI Service: Model={model}, max_tokens={max_tokens}, temperature={temperature}")
        logger.debug(f"AI Service: System prompt length: {len(system_prompt)} chars")
        logger.debug(f"AI Service: User prompt length: {len(user_prompt)} chars")
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    # Log detailed response if enabled
                    self._log_detailed_response(
                        response.status_code,
                        dict(response.headers),
                        is_stream=True
                    )
                    
                    # Log response status
                    logger.info(f"AI Service: Received response with status {response.status_code}")
                    
                    # Check Content-Type header for error responses
                    content_type = response.headers.get("content-type", "").lower()
                    if "application/json" in content_type and response.status_code == 200:
                        # For JSON responses with 200, we'll check the body for errors
                        pass  # Will be checked in stream processing
                    
                    # Check status before processing stream
                    if response.status_code >= 400:
                        # Read error response content
                        error_content = await response.aread()
                        error_text = error_content.decode('utf-8', errors='ignore') if error_content else ""
                        logger.error(f"AI Service: HTTP error {response.status_code} from {base_url}: {error_text}")
                        raise Exception(f"AI API error ({base_url}): {response.status_code} - {error_text}")
                    
                    # For 200 responses, check if it's actually an error by peeking at first few bytes
                    # Some proxies return 200 with error messages
                    if response.status_code == 200:
                        # We'll check the first line of the stream for error patterns
                        pass  # Will be checked in stream processing
                    
                    # Track streaming metrics
                    chunk_count = 0
                    total_chars = 0
                    first_line = True
                    error_detected = False
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        # Check first non-empty line for error messages (some proxies return errors in plain text)
                        if first_line:
                            first_line = False
                            line_lower = line.lower()
                            # Check for common error patterns even if status is 200
                            if any(keyword in line_lower for keyword in ["error", "unexpected", "not found", "invalid", "failed"]):
                                # This might be an error message, try to parse it
                                if not line.startswith("data: "):
                                    # Plain text error (not SSE format)
                                    logger.error(f"AI Service: Error message in response from {base_url}: {line}")
                                    raise Exception(f"AI API error ({base_url}): {line}")
                        
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                logger.debug(f"AI Service: Stream completed - received {chunk_count} chunks, {total_chars} characters")
                                break
                            
                            try:
                                data = json.loads(data_str)
                                
                                # Check for errors in the response
                                if "error" in data:
                                    error_detected = True
                                    error_msg = data["error"]
                                    if isinstance(error_msg, dict):
                                        error_msg = error_msg.get("message", str(error_msg))
                                    
                                    # Add helpful hint for endpoint errors
                                    if "endpoint" in str(error_msg).lower() or "unexpected" in str(error_msg).lower():
                                        if "/v1" not in base_url:
                                            error_msg = (
                                                f"{error_msg}. "
                                                f"Hint: Your base URL might be missing '/v1'. "
                                                f"Try: {base_url}/v1"
                                            )
                                    
                                    logger.error(f"AI Service: API returned error in stream from {base_url}: {error_msg}")
                                    logger.error(f"AI Service: Full error data: {data}")
                                    raise Exception(f"AI API error ({base_url}): {error_msg}")
                                
                                # Check for error-like patterns in the data structure
                                if isinstance(data, dict):
                                    # Some APIs return errors in different formats
                                    if "message" in data and any(keyword in str(data["message"]).lower() for keyword in ["error", "unexpected", "not found", "invalid"]):
                                        error_detected = True
                                        error_msg = data["message"]
                                        logger.error(f"AI Service: Error message detected in response from {base_url}: {error_msg}")
                                        raise Exception(f"AI API error ({base_url}): {error_msg}")
                                
                                # Extract content delta
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content_chunk = delta.get("content")
                                    
                                    if content_chunk:
                                        chunk_count += 1
                                        total_chars += len(content_chunk)
                                        yield content_chunk
                            
                            except json.JSONDecodeError as e:
                                # If we can't parse JSON and it looks like an error, raise it
                                if any(keyword in data_str.lower() for keyword in ["error", "unexpected", "not found", "invalid", "failed"]):
                                    logger.error(f"AI Service: Error message in non-JSON response from {base_url}: {data_str}")
                                    raise Exception(f"AI API error ({base_url}): {data_str}")
                                
                                logger.warning(f"AI Service: Failed to parse SSE chunk: {e}")
                                logger.debug(f"AI Service: Problematic data: {data_str[:200]}")
                                continue
                    
                    # If we got a 200 response but no content chunks and no error was detected, something might be wrong
                    if chunk_count == 0 and not error_detected and response.status_code == 200:
                        logger.warning(f"AI Service: Received 200 response but no content chunks were yielded")
                        # Don't raise here as some APIs might legitimately return empty responses
            
            logger.info(f"AI Service: Streaming analysis complete - {chunk_count} chunks, {total_chars} characters")
        
        except httpx.HTTPStatusError as e:
            # This shouldn't happen now since we check status before raise_for_status
            # But keep it as a fallback
            error_message = f"HTTP {e.response.status_code}"
            try:
                # Try to get error details if available
                if hasattr(e.response, 'text') and not hasattr(e.response, 'aread'):
                    error_message += f": {e.response.text}"
            except Exception:
                pass
            
            # Add helpful hint for common 404 errors
            base_url = self._get_base_url()
            if e.response.status_code == 404 and "/v1" not in base_url:
                error_message += f". Hint: Try adding '/v1' to your base URL: {base_url}/v1"
            
            logger.error(f"AI Service: HTTP error from {base_url} - {error_message}")
            logger.error(f"AI Service: Request URL was: {url}")
            raise Exception(f"AI API error ({base_url}): {error_message}")
        
        except httpx.RequestError as e:
            base_url = self._get_base_url()
            logger.error(f"AI Service: Request error from {base_url} - {type(e).__name__}: {e}")
            logger.error(f"AI Service: Request URL was: {url}")
            raise Exception(f"AI API connection error ({base_url}): {str(e)}")
        
        except Exception as e:
            base_url = self._get_base_url()
            logger.error(f"AI Service: Unexpected error during streaming from {base_url} - {type(e).__name__}: {e}", exc_info=True)
            logger.error(f"AI Service: Request URL was: {url}")
            raise
    
    async def analyze(
        self,
        content: str,
        prompt_type: str = "explain",
        custom_prompt: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Analyze content with AI and return complete response.
        
        Args:
            content: Content to analyze
            prompt_type: Type of analysis
            custom_prompt: Custom prompt template
            variables: Variables for prompt substitution
            
        Returns:
            Complete AI response
        """
        chunks = []
        async for chunk in self.analyze_stream(content, prompt_type, custom_prompt, variables):
            chunks.append(chunk)
        
        return "".join(chunks)
    
    async def test_connection(self) -> tuple[bool, str]:
        """
        Test connection to AI service.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        from app.core.config import AIConfig
        if not AIConfig.is_configured():
            logger.warning("AI Service: Test connection failed - service not configured")
            return False, "AI service not configured (missing API key or disabled)"
        
        try:
            # Get config values from AIConfig
            base_url = self._get_base_url()
            model = self._get_model()
            
            # Simple test with minimal content
            test_prompt = "Respond with 'OK' if you can read this."
            url = self._build_url("/chat/completions")
            
            logger.info(f"AI Service: Testing connection to {url}")
            logger.debug(f"AI Service: Test using model={model}")
            
            async with httpx.AsyncClient(timeout=10) as client:
                headers = self._build_headers()
                
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": test_prompt}],
                    "max_tokens": 10
                }
                
                # Log detailed request if enabled
                self._log_detailed_request("POST", url, headers, payload)
                
                response = await client.post(url, headers=headers, json=payload)
                
                logger.info(f"AI Service: Test connection received status {response.status_code}")
                
                # Read response body once for logging and parsing
                response_body = await response.aread()
                response_text = response_body.decode('utf-8', errors='ignore') if response_body else ""
                
                # Log detailed response if enabled
                if self._is_detailed_logging_enabled():
                    self._log_detailed_response(
                        response.status_code,
                        dict(response.headers),
                        response_text
                    )
                
                # Check for common configuration errors
                if response.status_code == 404:
                    error_str = response_text
                    logger.error(f"AI Service: Test connection failed (404) - {error_str[:200]}")
                    
                    # Check if it's a missing /v1 issue
                    if "not found" in error_str.lower() or "endpoint" in error_str.lower():
                        # Suggest adding /v1 if not present
                        if "/v1" not in base_url:
                            return False, (
                                f"Connection failed (404 Not Found). "
                                f"Hint: Your base URL might be missing '/v1'. "
                                f"Try: {base_url}/v1"
                            )
                        else:
                            return False, f"Connection failed (404 Not Found): {error_str[:200]}"
                    return False, f"Connection failed (404 Not Found): {error_str[:200]}"
                
                # Check for other errors
                if response.status_code >= 400:
                    error_str = response_text
                    logger.error(f"AI Service: Test connection failed ({response.status_code}) - {error_str[:200]}")
                    return False, f"Connection failed ({response.status_code}): {error_str[:200]}"
                
                response.raise_for_status()
                
                # Parse response to verify it's valid (use the text we already read)
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"AI Service: Could not parse response JSON: {e}")
                    return False, f"Invalid response format: {str(e)}"
                if "error" in data:
                    error_msg = data["error"]
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get("message", str(error_msg))
                    
                    logger.error(f"AI Service: Test connection returned error from {base_url} - {error_msg}")
                    
                    # Check if it's an endpoint error
                    if "endpoint" in str(error_msg).lower() and "/v1" not in base_url:
                        return False, (
                            f"API error ({base_url}): {error_msg}. "
                            f"Hint: Try adding '/v1' to your base URL: {base_url}/v1"
                        )
                    return False, f"API error ({base_url}): {error_msg}"
                
                logger.info(f"AI Service: Test connection successful - model={model}")
                return True, f"Connection successful (model: {model})"
        
        except httpx.HTTPStatusError as e:
            base_url = self._get_base_url()
            logger.error(f"AI Service: Test connection HTTP status error from {base_url} - {e.response.status_code}: {e.response.text[:100]}")
            return False, f"HTTP error ({base_url}): {e.response.status_code} - {e.response.text[:100]}"
        
        except httpx.RequestError as e:
            base_url = self._get_base_url()
            logger.error(f"AI Service: Test connection request error from {base_url} - {type(e).__name__}: {e}")
            return False, f"Connection error ({base_url}): {str(e)}"
        
        except Exception as e:
            base_url = self._get_base_url()
            logger.error(f"AI Service: Test connection unexpected error from {base_url} - {type(e).__name__}: {e}", exc_info=True)
            return False, f"Unexpected error ({base_url}): {str(e)}"
    
    async def get_available_models(self) -> list[str]:
        """
        Fetch available models from AI server.
        
        Returns:
            List of model IDs available on the server
        """
        from app.core.config import AIConfig
        if not AIConfig.is_configured():
            logger.warning("AI Service: Cannot fetch models - service not configured")
            return []
        
        try:
            base_url = self._get_base_url()
            url = self._build_url("/models")
            logger.info(f"AI Service: Fetching available models from {url}")
            
            async with httpx.AsyncClient(timeout=10) as client:
                headers = self._build_headers()
                
                # Log detailed request if enabled
                self._log_detailed_request("GET", url, headers)
                
                response = await client.get(url, headers=headers)
                
                # Read response body once for logging and parsing
                response_body = await response.aread()
                response_text = response_body.decode('utf-8', errors='ignore') if response_body else ""
                
                # Log detailed response if enabled
                if self._is_detailed_logging_enabled():
                    self._log_detailed_response(
                        response.status_code,
                        dict(response.headers),
                        response_text
                    )
                
                if response.status_code == 404:
                    base_url = self._get_base_url()
                    logger.warning(f"AI Service: Server does not support /models endpoint (404) from {base_url}")
                    return []
                
                response.raise_for_status()
                
                # Parse JSON from the text we already read
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    base_url = self._get_base_url()
                    logger.warning(f"AI Service: Could not parse response JSON from {base_url}: {e}")
                    return []
                
                # OpenAI format: { "object": "list", "data": [{"id": "model-name", ...}] }
                if "data" in data and isinstance(data["data"], list):
                    models = [m["id"] for m in data["data"] if "id" in m]
                    logger.info(f"AI Service: Found {len(models)} models")
                    logger.debug(f"AI Service: Models: {models}")
                    return models
                
                logger.warning(f"AI Service: Unexpected response format: {data}")
                return []
        
        except httpx.HTTPStatusError as e:
            base_url = self._get_base_url()
            logger.warning(f"AI Service: HTTP error fetching models from {base_url} - {e.response.status_code}")
            return []
        
        except httpx.RequestError as e:
            base_url = self._get_base_url()
            logger.warning(f"AI Service: Request error fetching models from {base_url} - {type(e).__name__}: {e}")
            return []
        
        except Exception as e:
            base_url = self._get_base_url()
            logger.error(f"AI Service: Unexpected error fetching models from {base_url} - {type(e).__name__}: {e}", exc_info=True)
            return []


# Global AI service instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    Get the singleton AIService instance.
    Since AIService is stateless and reads directly from AIConfig,
    we can use a simple singleton pattern without comparison logic.
    """
    global _ai_service
    
    if _ai_service is None:
        logger.debug("AI Service: Creating new service instance")
        _ai_service = AIService()
    
    return _ai_service


def reset_ai_service():
    global _ai_service
    _ai_service = None

