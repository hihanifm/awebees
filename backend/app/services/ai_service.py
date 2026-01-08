"""OpenAI-compatible API service for AI-powered analysis."""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncIterator
import httpx

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered analysis using OpenAI-compatible APIs."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        timeout: int = 60
    ):
        """
        Initialize AI service.
        
        Args:
            base_url: API base URL (default: https://api.openai.com/v1)
            api_key: API key (default: from OPENAI_API_KEY env var)
            model: Model name (default: gpt-4o-mini)
            max_tokens: Max tokens in response
            temperature: Sampling temperature (0-2)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("AI Service: No API key configured. AI features will be disabled.")
    
    def is_configured(self) -> bool:
        """Check if AI service is properly configured."""
        return bool(self.api_key)
    
    def get_system_prompt(self, prompt_type: str) -> str:
        """Get predefined system prompt by type."""
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
            
            # Substitute variables if provided
            if variables:
                for key, value in variables.items():
                    placeholder = "{" + key + "}"
                    if placeholder in prompt:
                        prompt = prompt.replace(placeholder, str(value))
            
            # Append content if not already included
            if "{result_content}" not in custom_prompt:
                prompt += f"\n\n{content}"
            else:
                prompt = prompt.replace("{result_content}", content)
        else:
            # Use predefined prompt
            prompt = content
        
        return prompt
    
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
        if not self.is_configured():
            raise ValueError("AI service is not configured. Please set OPENAI_API_KEY.")
        
        # Build prompts
        system_prompt = self.get_system_prompt(prompt_type)
        user_prompt = self.build_prompt(content, prompt_type, custom_prompt, variables)
        
        logger.info(f"AI Service: Starting streaming analysis (model: {self.model}, prompt_type: {prompt_type})")
        
        # Prepare request
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True
        }
        
        # Log request details (truncate content for readability)
        logger.info(f"AI Service: Sending request to {url}")
        logger.debug(f"AI Service: Model={self.model}, max_tokens={self.max_tokens}, temperature={self.temperature}")
        logger.debug(f"AI Service: System prompt length: {len(system_prompt)} chars")
        logger.debug(f"AI Service: User prompt length: {len(user_prompt)} chars")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    # Log response status
                    logger.info(f"AI Service: Received response with status {response.status_code}")
                    
                    # Check status before processing stream
                    if response.status_code >= 400:
                        # Read error response content
                        error_content = await response.aread()
                        error_text = error_content.decode('utf-8', errors='ignore') if error_content else ""
                        logger.error(f"AI Service: HTTP error {response.status_code}: {error_text}")
                        raise Exception(f"AI API error: {response.status_code} - {error_text}")
                    
                    # Track streaming metrics
                    chunk_count = 0
                    total_chars = 0
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                logger.debug(f"AI Service: Stream completed - received {chunk_count} chunks, {total_chars} characters")
                                break
                            
                            try:
                                data = json.loads(data_str)
                                
                                # Check for errors in the response
                                if "error" in data:
                                    error_msg = data["error"]
                                    if isinstance(error_msg, dict):
                                        error_msg = error_msg.get("message", str(error_msg))
                                    
                                    # Add helpful hint for endpoint errors
                                    if "endpoint" in str(error_msg).lower() or "unexpected" in str(error_msg).lower():
                                        if "/v1" not in self.base_url:
                                            error_msg = (
                                                f"{error_msg}. "
                                                f"Hint: Your base URL might be missing '/v1'. "
                                                f"Try: {self.base_url}/v1"
                                            )
                                    
                                    logger.error(f"AI Service: API returned error in stream: {error_msg}")
                                    logger.error(f"AI Service: Full error data: {data}")
                                    raise Exception(f"AI API error: {error_msg}")
                                
                                # Extract content delta
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content_chunk = delta.get("content")
                                    
                                    if content_chunk:
                                        chunk_count += 1
                                        total_chars += len(content_chunk)
                                        yield content_chunk
                            
                            except json.JSONDecodeError as e:
                                logger.warning(f"AI Service: Failed to parse SSE chunk: {e}")
                                logger.debug(f"AI Service: Problematic data: {data_str[:200]}")
                                continue
            
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
            if e.response.status_code == 404 and "/v1" not in self.base_url:
                error_message += f". Hint: Try adding '/v1' to your base URL: {self.base_url}/v1"
            
            logger.error(f"AI Service: HTTP error - {error_message}")
            logger.error(f"AI Service: Request URL was: {url}")
            raise Exception(f"AI API error: {error_message}")
        
        except httpx.RequestError as e:
            logger.error(f"AI Service: Request error - {type(e).__name__}: {e}")
            logger.error(f"AI Service: Request URL was: {url}")
            raise Exception(f"AI API connection error: {str(e)}")
        
        except Exception as e:
            logger.error(f"AI Service: Unexpected error during streaming - {type(e).__name__}: {e}", exc_info=True)
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
        if not self.is_configured():
            logger.warning("AI Service: Test connection failed - service not configured")
            return False, "AI service not configured (missing API key)"
        
        try:
            # Simple test with minimal content
            test_prompt = "Respond with 'OK' if you can read this."
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            
            logger.info(f"AI Service: Testing connection to {url}")
            logger.debug(f"AI Service: Test using model={self.model}")
            
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": test_prompt}],
                    "max_tokens": 10
                }
                
                response = await client.post(url, headers=headers, json=payload)
                
                logger.info(f"AI Service: Test connection received status {response.status_code}")
                
                # Check for common configuration errors
                if response.status_code == 404:
                    error_text = await response.aread()
                    error_str = error_text.decode('utf-8', errors='ignore')
                    
                    logger.error(f"AI Service: Test connection failed (404) - {error_str[:200]}")
                    
                    # Check if it's a missing /v1 issue
                    if "not found" in error_str.lower() or "endpoint" in error_str.lower():
                        # Suggest adding /v1 if not present
                        if "/v1" not in self.base_url:
                            return False, (
                                f"Connection failed (404 Not Found). "
                                f"Hint: Your base URL might be missing '/v1'. "
                                f"Try: {self.base_url}/v1"
                            )
                        else:
                            return False, f"Connection failed (404 Not Found): {error_str[:200]}"
                    return False, f"Connection failed (404 Not Found): {error_str[:200]}"
                
                # Check for other errors
                if response.status_code >= 400:
                    error_text = await response.aread()
                    error_str = error_text.decode('utf-8', errors='ignore')
                    logger.error(f"AI Service: Test connection failed ({response.status_code}) - {error_str[:200]}")
                    return False, f"Connection failed ({response.status_code}): {error_str[:200]}"
                
                response.raise_for_status()
                
                # Parse response to verify it's valid
                data = response.json()
                if "error" in data:
                    error_msg = data["error"]
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get("message", str(error_msg))
                    
                    logger.error(f"AI Service: Test connection returned error - {error_msg}")
                    
                    # Check if it's an endpoint error
                    if "endpoint" in str(error_msg).lower() and "/v1" not in self.base_url:
                        return False, (
                            f"API error: {error_msg}. "
                            f"Hint: Try adding '/v1' to your base URL: {self.base_url}/v1"
                        )
                    return False, f"API error: {error_msg}"
                
                logger.info(f"AI Service: Test connection successful - model={self.model}")
                return True, f"Connection successful (model: {self.model})"
        
        except httpx.HTTPStatusError as e:
            logger.error(f"AI Service: Test connection HTTP status error - {e.response.status_code}: {e.response.text[:100]}")
            return False, f"HTTP error {e.response.status_code}: {e.response.text[:100]}"
        
        except httpx.RequestError as e:
            logger.error(f"AI Service: Test connection request error - {type(e).__name__}: {e}")
            return False, f"Connection error: {str(e)}"
        
        except Exception as e:
            logger.error(f"AI Service: Test connection unexpected error - {type(e).__name__}: {e}", exc_info=True)
            return False, f"Unexpected error: {str(e)}"


# Global AI service instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create the global AI service instance."""
    global _ai_service
    if _ai_service is None:
        from app.core.config import AIConfig
        _ai_service = AIService(
            base_url=AIConfig.BASE_URL,
            api_key=AIConfig.API_KEY,
            model=AIConfig.MODEL,
            max_tokens=AIConfig.MAX_TOKENS,
            temperature=AIConfig.TEMPERATURE,
            timeout=AIConfig.TIMEOUT
        )
    return _ai_service


def reset_ai_service():
    """Reset the global AI service instance (useful for testing or config changes)."""
    global _ai_service
    _ai_service = None

