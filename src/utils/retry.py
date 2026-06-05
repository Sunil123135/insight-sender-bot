"""
Module: src/utils/retry.py
Purpose: Async retry decorator with exponential backoff
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - tenacity (retry policies)

Used by:
    - src.scrapers.*
    - src.processors.summarizer
    - src.email.sender
"""

# Standard library
from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

# Third-party
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

P = ParamSpec("P")
T = TypeVar("T")


def async_retry(
    max_retries: int = 3,
    backoff_multiplier: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]],
    Callable[P, Coroutine[Any, Any, T]],
]:
    """Create an async retry decorator.

    Args:
        max_retries: Maximum number of attempts.
        backoff_multiplier: Exponential multiplier.
        initial_delay: Initial retry delay in seconds.
        max_delay: Maximum retry delay in seconds.
        exceptions: Exception types eligible for retry.

    Returns:
        Decorator for async callables.
    """
    decorator = retry(
        reraise=True,
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(
            multiplier=initial_delay,
            exp_base=backoff_multiplier,
            max=max_delay,
        ),
        retry=retry_if_exception_type(exceptions),
    )
    return decorator
