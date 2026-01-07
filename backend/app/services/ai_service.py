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
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(data_str)
                                
                                # Extract content delta
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content_chunk = delta.get("content")
                                    
                                    if content_chunk:
                                        yield content_chunk
                            
                            except json.JSONDecodeError as e:
                                logger.warning(f"AI Service: Failed to parse SSE chunk: {e}")
                                continue
            
            logger.info("AI Service: Streaming analysis complete")
        
        except httpx.HTTPStatusError as e:
            logger.error(f"AI Service: HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"AI API error: {e.response.status_code} - {e.response.text}")
        
        except httpx.RequestError as e:
            logger.error(f"AI Service: Request error: {e}")
            raise Exception(f"AI API connection error: {str(e)}")
        
        except Exception as e:
            logger.error(f"AI Service: Unexpected error: {e}", exc_info=True)
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
            return False, "AI service not configured (missing API key)"
        
        try:
            # Simple test with minimal content
            test_prompt = "Respond with 'OK' if you can read this."
            
            async with httpx.AsyncClient(timeout=10) as client:
                url = f"{self.base_url.rstrip('/')}/chat/completions"
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
                response.raise_for_status()
                
                return True, f"Connection successful (model: {self.model})"
        
        except httpx.HTTPStatusError as e:
            return False, f"HTTP error {e.response.status_code}: {e.response.text[:100]}"
        
        except httpx.RequestError as e:
            return False, f"Connection error: {str(e)}"
        
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"


# Global AI service instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create the global AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def reset_ai_service():
    """Reset the global AI service instance (useful for testing or config changes)."""
    global _ai_service
    _ai_service = None

