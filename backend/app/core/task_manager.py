"""Task manager for tracking and cancelling analysis tasks."""

import asyncio
import uuid
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnalysisTask:
    """Represents an active analysis task."""
    task_id: str
    cancellation_event: asyncio.Event
    status: str = "running"  # running, completed, cancelled, error
    created_at: float = field(default_factory=time.time)
    progress_info: Dict = field(default_factory=dict)


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
    
    def cleanup_task(self, task_id: str):
        """
        Remove a task from the registry.
        
        Args:
            task_id: Task ID to cleanup
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.debug(f"TaskManager: Cleaned up task {task_id}")
    
    def cleanup_old_tasks(self):
        """Remove completed/cancelled tasks older than cleanup_interval."""
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
    """Get the global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

