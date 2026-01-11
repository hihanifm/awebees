import asyncio
import uuid
import time
import tempfile
import shutil
import contextvars
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# Context variable for current task ID (accessible anywhere in the async call chain)
# This allows accessing task_id without passing it through every function parameter
_current_task_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('current_task_id', default=None)

# Export for use in analyze route
__all__ = ['_current_task_id']


@dataclass
class AnalysisTask:
    """Represents an active analysis task."""
    task_id: str
    cancellation_event: asyncio.Event
    status: str = "running"  # running, completed, cancelled, error
    created_at: float = field(default_factory=time.time)
    progress_info: Dict = field(default_factory=dict)
    temp_dir: Optional[Path] = None  # Temporary directory for extracted zip files


class TaskManager:
    """Manages active analysis tasks and cancellation."""
    
    def __init__(self):
        self._tasks: Dict[str, AnalysisTask] = {}
        self._cleanup_interval = 300  # 5 minutes
    
    def create_task(self) -> str:
        """
        Create a new analysis task.
        
        Returns:
            Task ID (UUID string)
        """
        task_id = str(uuid.uuid4())
        cancellation_event = asyncio.Event()
        
        self._tasks[task_id] = AnalysisTask(
            task_id=task_id,
            cancellation_event=cancellation_event
        )
        
        logger.debug(f"TaskManager: Created task {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[AnalysisTask]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            AnalysisTask if found, None otherwise
        """
        return self._tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task by setting its cancellation event.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if task was found and cancelled, False otherwise
        """
        task = self._tasks.get(task_id)
        if task:
            task.cancellation_event.set()
            task.status = "cancelled"
            logger.info(f"TaskManager: Cancelled task {task_id}")
            return True
        logger.warning(f"TaskManager: Task {task_id} not found for cancellation")
        return False
    
    def update_task_status(self, task_id: str, status: str, progress_info: Optional[Dict] = None):
        """
        Update task status and progress info.
        
        Args:
            task_id: Task ID
            status: New status (running, completed, cancelled, error)
            progress_info: Optional progress information dict
        """
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            if progress_info:
                task.progress_info.update(progress_info)
    
    def get_current_task_id(self) -> Optional[str]:
        """
        Get the current task ID from context variable.
        
        Returns:
            Current task ID if set in context, None otherwise
        """
        return _current_task_id.get()
    
    def get_task_temp_dir(self, task_id: Optional[str] = None) -> Optional[Path]:
        """
        Get or create a temporary directory for a task.
        
        Used for storing extracted zip files during analysis.
        If task_id is not provided, tries to get it from context variable.
        
        Args:
            task_id: Task ID (optional, will use context variable if not provided)
            
        Returns:
            Path to temporary directory, or None if task not found
        """
        if task_id is None:
            task_id = _current_task_id.get()
        
        if task_id is None:
            return None
            
        task = self._tasks.get(task_id)
        if not task:
            return None
        
        if task.temp_dir is None:
            # Create a temporary directory for this task
            temp_dir = Path(tempfile.mkdtemp(prefix=f"lens_task_{task_id}_"))
            task.temp_dir = temp_dir
            logger.debug(f"TaskManager: Created temp directory {temp_dir} for task {task_id}")
        
        return task.temp_dir
    
    def cleanup_task_temp_dir(self, task_id: str) -> bool:
        """
        Clean up temporary directory for a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if cleanup was performed, False if task not found or no temp dir
        """
        task = self._tasks.get(task_id)
        if not task or task.temp_dir is None:
            return False
        
        try:
            if task.temp_dir.exists():
                shutil.rmtree(task.temp_dir)
                logger.debug(f"TaskManager: Cleaned up temp directory {task.temp_dir} for task {task_id}")
            task.temp_dir = None
            return True
        except Exception as e:
            logger.warning(f"TaskManager: Error cleaning up temp directory {task.temp_dir} for task {task_id}: {e}")
            return False
    
    def cleanup_task(self, task_id: str):
        """
        Remove a task from the registry and clean up its temporary directory.
        
        Args:
            task_id: Task ID to cleanup
        """
        # Clean up temp directory first
        self.cleanup_task_temp_dir(task_id)
        
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.debug(f"TaskManager: Cleaned up task {task_id}")
    
    def cleanup_old_tasks(self):
        current_time = time.time()
        tasks_to_remove = []
        
        for task_id, task in self._tasks.items():
            if task.status in ("completed", "cancelled", "error"):
                age = current_time - task.created_at
                if age > self._cleanup_interval:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            self.cleanup_task(task_id)
        
        if tasks_to_remove:
            logger.debug(f"TaskManager: Cleaned up {len(tasks_to_remove)} old task(s)")


# Global task manager instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

