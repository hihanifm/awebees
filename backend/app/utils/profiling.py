"""Profiling utilities for performance analysis."""

import os
import cProfile
import pstats
import io
import logging
from functools import wraps
from typing import Callable, Any, Iterator
import inspect

logger = logging.getLogger(__name__)

# Check if profiling is enabled via environment variable
_PROFILING_ENABLED = os.getenv("ENABLE_PROFILING", "false").lower() in ("true", "1", "yes")


def profile(log_interval: int = 100, top_n: int = 20):
    """
    Decorator to profile function execution using cProfile.
    
    Automatically detects if the function is a generator and handles it appropriately.
    For generators, logs stats periodically. For regular functions, logs stats at completion.
    
    Args:
        log_interval: For generators, log stats every N iterations (default: 100)
        top_n: Number of top functions to show in stats (default: 20)
    
    Usage:
        @profile
        def my_function():
            ...
        
        @profile(log_interval=50, top_n=10)
        def my_generator():
            ...
    """
    def decorator(func: Callable) -> Callable:
        if not _PROFILING_ENABLED:
            # Profiling disabled, return function as-is
            return func
        
        # Check if function is a generator
        is_generator = inspect.isgeneratorfunction(func)
        
        if is_generator:
            @wraps(func)
            def generator_wrapper(*args, **kwargs) -> Iterator[Any]:
                profiler = cProfile.Profile()
                profiler.enable()
                iteration_count = 0
                
                try:
                    gen = func(*args, **kwargs)
                    for item in gen:
                        iteration_count += 1
                        yield item
                        
                        # Log profiling stats periodically
                        if iteration_count % log_interval == 0:
                            profiler.disable()
                            s = io.StringIO()
                            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                            ps.print_stats(top_n)
                            logger.debug(f"Profile [{func.__name__}] (iteration {iteration_count}):\n{s.getvalue()}")
                            profiler.enable()
                finally:
                    profiler.disable()
                    # Log final profiling stats
                    s = io.StringIO()
                    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                    ps.print_stats(top_n)
                    logger.info(f"Profile [{func.__name__}] final (total iterations: {iteration_count}):\n{s.getvalue()}")
            
            return generator_wrapper
        else:
            @wraps(func)
            def function_wrapper(*args, **kwargs) -> Any:
                profiler = cProfile.Profile()
                profiler.enable()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    profiler.disable()
                    # Log profiling stats
                    s = io.StringIO()
                    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                    ps.print_stats(top_n)
                    logger.info(f"Profile [{func.__name__}]:\n{s.getvalue()}")
            
            return function_wrapper
    
    return decorator

