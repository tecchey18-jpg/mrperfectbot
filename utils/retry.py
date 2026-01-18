"""
Retry Logic with Exponential Backoff
Handles transient failures gracefully
"""

import asyncio
import random
import logging
from functools import wraps
from dataclasses import dataclass
from typing import Callable, Any, Optional, Tuple, Type

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_range: Tuple[float, float] = (0.5, 1.5)
    
    # Exceptions that should trigger retry
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    
    # Exceptions that should NOT retry
    fatal_exceptions: Tuple[Type[Exception], ...] = ()


def calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool,
    jitter_range: Tuple[float, float]
) -> float:
    """Calculate delay for given attempt with exponential backoff and jitter"""
    delay = base_delay * (exponential_base ** attempt)
    delay = min(delay, max_delay)
    
    if jitter:
        jitter_factor = random.uniform(jitter_range[0], jitter_range[1])
        delay *= jitter_factor
    
    return delay


def async_retry(config: Optional[RetryConfig] = None):
    """
    Decorator for async functions with retry logic
    
    Usage:
        @async_retry(RetryConfig(max_attempts=5))
        async def my_function():
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except config.fatal_exceptions as e:
                    # Don't retry fatal exceptions
                    logger.error(f"Fatal exception in {func.__name__}: {e}")
                    raise
                    
                except config.retry_exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(
                            attempt,
                            config.base_delay,
                            config.max_delay,
                            config.exponential_base,
                            config.jitter,
                            config.jitter_range
                        )
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    return decorator


class RetryContext:
    """
    Context manager for retry logic
    
    Usage:
        async with RetryContext(max_attempts=3) as ctx:
            while ctx.should_retry():
                try:
                    result = await some_operation()
                    break
                except Exception as e:
                    await ctx.handle_exception(e)
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.attempt = 0
        self.last_exception = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def should_retry(self) -> bool:
        """Check if more attempts are available"""
        return self.attempt < self.config.max_attempts
    
    async def handle_exception(self, exception: Exception) -> None:
        """Handle exception and prepare for retry"""
        self.last_exception = exception
        self.attempt += 1
        
        if isinstance(exception, self.config.fatal_exceptions):
            raise exception
        
        if self.attempt < self.config.max_attempts:
            delay = calculate_delay(
                self.attempt - 1,
                self.config.base_delay,
                self.config.max_delay,
                self.config.exponential_base,
                self.config.jitter,
                self.config.jitter_range
            )
            
            logger.warning(
                f"Attempt {self.attempt}/{self.config.max_attempts} failed: {exception}. "
                f"Retrying in {delay:.2f}s..."
            )
            
            await asyncio.sleep(delay)
        else:
            raise exception
