from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Awaitable, Any
import asyncio
import logging
import re
import hashlib
from pathlib import Path
from app.core.models import InsightResult, ProgressEvent

logger = logging.getLogger(__name__)


class Insight(ABC):
    """Base class for all insights."""
    
    @property
    def id(self) -> str:
        """
        Unique identifier for this insight (auto-generated from file path).
        
        For class-based insights, this is automatically generated from the file path
        by the plugin manager. If you need to override it (not recommended), you can
        do so in your class, but it's better to let the system auto-generate it.
        """
        raise NotImplementedError("ID should be auto-generated from file path. If you see this error, the insight was not properly wrapped by the plugin manager.")
    
    @staticmethod
    def _normalize_for_id(text: str) -> str:
        """Normalize text for use in ID: lowercase, alphanumeric + underscores only."""
        return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')
    
    @staticmethod
    def _generate_id_from_path(
        file_path: Path,
        insights_root: Path,
        source: str
    ) -> str:
        """
        Generate insight ID from file path.
        
        Args:
            file_path: Path to the insight file
            insights_root: Root directory for insights
            source: Source identifier (built-in or external path)
            
        Returns:
            Generated ID string
        """
        try:
            relative_path = file_path.relative_to(insights_root)
        except ValueError:
            relative_path = file_path
        
        relative_stem = relative_path.with_suffix('')
        
        if source == "built-in":
            parts = [p for p in relative_stem.parts if p != '.']
            normalized_parts = [Insight._normalize_for_id(p) for p in parts]
            return '_'.join(normalized_parts) if normalized_parts else 'insight'
        else:
            source_hash = hashlib.md5(source.encode()).hexdigest()[:8]
            parts = [p for p in relative_stem.parts if p != '.']
            normalized_parts = [Insight._normalize_for_id(p) for p in parts]
            base_id = '_'.join(normalized_parts) if normalized_parts else 'insight'
            return f"ext_{source_hash}_{base_id}"
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    async def analyze(
        self,
        user_path: str,
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        pass
    
    def _get_path_files(self, user_path: str) -> List[str]:
        """
        Get files for a single user path (if folder, list recursively; if file, use directly; if zip file, list contents).
        
        Args:
            user_path: User input path (file or folder)
            
        Returns:
            List of file paths (or virtual zip paths for files inside zip archives)
        """
        from app.services.file_handler import is_zip_file, list_zip_contents
        
        path_obj = Path(user_path)
        if not path_obj.exists():
            logger.warning(f"{self.__class__.__name__}: Path does not exist: {user_path}")
            return []
        
        if path_obj.is_file():
            resolved_path = str(path_obj.resolve())
            # Check if it's a zip file - if so, list its contents
            if is_zip_file(resolved_path):
                logger.info(f"{self.__class__.__name__}: Expanding zip file: {resolved_path}")
                try:
                    zip_files = list_zip_contents(resolved_path, recursive=True)
                    logger.debug(f"{self.__class__.__name__}: Found {len(zip_files)} file(s) inside zip {resolved_path}")
                    return zip_files
                except Exception as e:
                    logger.error(f"{self.__class__.__name__}: Error listing zip contents {resolved_path}: {e}", exc_info=True)
                    # Fall back to treating it as a regular file
                    logger.warning(f"{self.__class__.__name__}: Falling back to treating {resolved_path} as regular file")
                    return [resolved_path]
            else:
                return [resolved_path]
        elif path_obj.is_dir():
            files = [str(p.resolve()) for p in path_obj.rglob("*") if p.is_file()]
            return sorted(files)
        else:
            return []
    
    def _check_file_limit(self, file_paths: List[str], user_path: str) -> Optional[InsightResult]:
        """
        Check if file count exceeds the maximum limit.
        
        Args:
            file_paths: List of file paths to check
            user_path: Original user input path
            
        Returns:
            InsightResult with error message if limit exceeded, None otherwise
        """
        from app.core.config import AppConfig
        
        max_files = AppConfig.MAX_FILES
        file_count = len(file_paths)
        
        if file_count > max_files:
            logger.warning(f"{self.__class__.__name__}: File limit exceeded - {file_count} files exceeds maximum of {max_files} files")
            error_message = f"""Error: Maximum file limit exceeded

The analysis path contains {file_count} files, which exceeds the maximum allowed limit of {max_files} files.

To proceed, please:
- Reduce the number of files in the selected path, or
- Use more specific file filter patterns to narrow down the files, or
- Increase the limit by setting INSIGHT_MAX_FILES environment variable (currently: {max_files})

Path: {user_path}"""
            return InsightResult(
                result_type="text",
                content=error_message,
                metadata={
                    "user_path": user_path,
                    "file_count": file_count,
                    "max_files": max_files,
                    "error": True
                }
            )
        
        return None
    
    @property
    def ai_enabled(self) -> bool: return True
    
    @property
    def ai_auto(self) -> bool: return False
    
    @property
    def ai_prompt_type(self) -> str:
        return "explain"
    
    @property
    def ai_custom_prompt(self) -> Optional[str]: return None
    
    @property
    def ai_prompt_variables(self) -> Optional[dict]: return None
    
    def get_context_param(self, key: str, default: Any = None) -> Any:
        """
        Get a parameter from the analysis context.
        
        This allows insights to access custom parameters and other context data
        (like task_id) that was set for the current analysis.
        
        Args:
            key: Parameter key (e.g., "task_id", "android_package_name")
            default: Default value if key not found
            
        Returns:
            Parameter value or default
            
        Example:
            package_name = self.get_context_param("android_package_name")
            task_id = self.get_context_param("task_id")
        """
        from app.core.task_manager import get_context_param as _get_context_param
        return _get_context_param(key, default)
    
    async def analyze_with_ai(
        self,
        user_path: str,
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """
        Wrapper around analyze() that automatically triggers AI analysis if ai_auto is True.
        """
        result = await self.analyze(user_path, cancellation_event, progress_callback)
        
        result.ai_enabled = self.ai_enabled
        result.ai_auto = self.ai_auto
        result.ai_prompt_type = self.ai_prompt_type
        result.ai_custom_prompt = self.ai_custom_prompt
        
        if self.ai_auto and self.ai_enabled:
            logger.info(f"AI Auto-trigger: Checking if AI should auto-run for insight (ai_auto={self.ai_auto}, ai_enabled={self.ai_enabled})")
            
            # Skip AI analysis if there is no data in the result
            if not result.content or not result.content.strip():
                logger.info(f"AI Auto-trigger: Skipping AI analysis - result content is empty or whitespace-only")
                return result
            
            from app.core.config import AIConfig
            
            logger.info(f"AI Auto-trigger: AIConfig.is_configured()={AIConfig.is_configured()}, ENABLED={AIConfig.ENABLED}, API_KEY={'set' if AIConfig.API_KEY else 'not set'}")
            
            if AIConfig.is_configured():
                try:
                    logger.info(f"AI Auto-trigger: Starting auto-analysis with prompt_type={self.ai_prompt_type}")
                    from app.services.ai_service import get_ai_service
                    ai_service = get_ai_service()
                    
                    ai_result = await ai_service.analyze(
                        content=result.content,
                        prompt_type=self.ai_prompt_type,
                        custom_prompt=self.ai_custom_prompt
                    )
                    
                    result.ai_analysis = ai_result
                    logger.info(f"AI Auto-trigger: Auto-analysis completed successfully")
                except Exception as e:
                    # Log error but don't fail the entire analysis
                    # Store error message so frontend can display it
                    error_msg = str(e)
                    
                    # Format error message to be more user-friendly
                    # Remove technical prefixes if present
                    if error_msg.startswith("AI API error: "):
                        error_msg = error_msg.replace("AI API error: ", "", 1)
                    elif error_msg.startswith("AI API connection error: "):
                        error_msg = error_msg.replace("AI API connection error: ", "", 1)
                    
                    # Provide helpful hints for common errors
                    if "endpoint" in error_msg.lower() or "unexpected" in error_msg.lower():
                        if "/v1" not in error_msg:
                            error_msg = (
                                f"{error_msg}\n\n"
                                f"💡 Tip: Make sure your AI Base URL includes '/v1' at the end "
                                f"(e.g., https://api.openai.com/v1 or http://localhost:1234/v1)"
                            )
                    elif "401" in error_msg or "unauthorized" in error_msg.lower():
                        error_msg = (
                            f"{error_msg}\n\n"
                            f"💡 Tip: Check that your API key is correct and has the necessary permissions."
                        )
                    elif "404" in error_msg or "not found" in error_msg.lower():
                        error_msg = (
                            f"{error_msg}\n\n"
                            f"💡 Tip: Verify that your AI Base URL is correct and the endpoint exists."
                        )
                    elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                        error_msg = (
                            f"{error_msg}\n\n"
                            f"💡 Tip: Check your network connection and ensure the AI service is accessible."
                        )
                    
                    result.ai_analysis_error = error_msg
                    logger.warning(f"AI auto-analysis failed: {error_msg}", exc_info=True)
            else:
                logger.warning(f"AI Auto-trigger: AI is not configured - skipping auto-analysis")
                result.ai_analysis_error = "AI is not configured. Please enable AI in settings."
        
        return result


class InsightIDWrapper(Insight):
    """
    Wrapper class that injects an auto-generated ID into a class-based insight instance.
    
    This allows class-based insights to have IDs generated from file paths, just like
    config-based insights, without requiring changes to the insight class itself.
    """
    
    def __init__(self, insight: Insight, generated_id: str):
        """
        Wrap an insight instance with an auto-generated ID.
        
        Args:
            insight: The insight instance to wrap
            generated_id: The ID to use (generated from file path)
        """
        self._insight = insight
        self._generated_id = generated_id
    
    @property
    def id(self) -> str:
        """Return the auto-generated ID."""
        return self._generated_id
    
    @property
    def name(self) -> str:
        """Delegate to wrapped insight."""
        return self._insight.name
    
    @property
    def description(self) -> str:
        """Delegate to wrapped insight."""
        return self._insight.description
    
    async def analyze(
        self,
        user_path: str,
        cancellation_event: Optional[asyncio.Event] = None,
        progress_callback: Optional[Callable[[ProgressEvent], Awaitable[None]]] = None
    ) -> InsightResult:
        """Delegate to wrapped insight."""
        return await self._insight.analyze(user_path, cancellation_event, progress_callback)
    
    def __getattr__(self, name: str):
        """Delegate all other attribute access to the wrapped insight."""
        return getattr(self._insight, name)