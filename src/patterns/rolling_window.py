"""Rolling window parallelism pattern for bounded concurrent processing."""

import asyncio
from collections import deque
from typing import Any, Awaitable, Callable, List, TypeVar

T = TypeVar('T')
R = TypeVar('R')


async def process_with_rolling_window(
    entities: List[T],
    process_fn: Callable[[T], Awaitable[R]],
    max_concurrent: int = 5
) -> List[R]:
    """
    Process entities in parallel using rolling window pattern.

    This pattern maintains a fixed number of concurrent tasks, starting new tasks
    immediately as previous ones complete. This ensures continuous processing
    without overwhelming system resources or external APIs.

    Algorithm:
    1. Initialize queue with all entities
    2. Start initial batch (up to max_concurrent)
    3. When any task completes:
       - Collect result
       - Start next task from queue if available
    4. Continue until all tasks complete

    Args:
        entities: List of entities to process
        process_fn: Async function to process each entity
        max_concurrent: Maximum number of parallel operations

    Returns:
        List of results from processing each entity

    Raises:
        Exception: If any processing task fails

    Example:
        >>> async def fetch_entity(entity_id: str) -> dict:
        ...     # Fetch from API
        ...     return {"id": entity_id, "data": "..."}
        ...
        >>> entity_ids = ["id1", "id2", "id3", ...]
        >>> results = await process_with_rolling_window(
        ...     entities=entity_ids,
        ...     process_fn=fetch_entity,
        ...     max_concurrent=5
        ... )
    """
    if not entities:
        return []

    remaining = deque(entities)
    running = {}  # task -> entity
    results = []

    # Start initial batch
    while len(running) < max_concurrent and remaining:
        entity = remaining.popleft()
        task = asyncio.create_task(process_fn(entity))
        running[task] = entity

    # Process as they complete
    while running:
        done, pending = await asyncio.wait(
            running.keys(),
            return_when=asyncio.FIRST_COMPLETED
        )

        for completed_task in done:
            entity = running.pop(completed_task)

            # Get result (may raise exception)
            try:
                result = completed_task.result()
                results.append(result)
            except Exception as e:
                # Re-raise with context about which entity failed
                raise Exception(f"Failed to process entity {entity}: {str(e)}") from e

            # Start next if available
            if remaining:
                next_entity = remaining.popleft()
                next_task = asyncio.create_task(process_fn(next_entity))
                running[next_task] = next_entity

    return results


class RollingWindowProgress:
    """
    Progress tracker for rolling window processing.

    Provides real-time progress information during rolling window execution.
    """

    def __init__(self, total: int):
        """Initialize progress tracker.

        Args:
            total: Total number of items to process
        """
        self.total = total
        self.completed = 0
        self.failed = 0
        self.in_progress = 0

    def increment_completed(self) -> None:
        """Increment completed count."""
        self.completed += 1
        self.in_progress -= 1

    def increment_failed(self) -> None:
        """Increment failed count."""
        self.failed += 1
        self.in_progress -= 1

    def set_in_progress(self, count: int) -> None:
        """Set current in-progress count."""
        self.in_progress = count

    @property
    def percentage(self) -> float:
        """Get completion percentage."""
        if self.total == 0:
            return 100.0
        return (self.completed + self.failed) / self.total * 100

    @property
    def remaining(self) -> int:
        """Get remaining items count."""
        return self.total - self.completed - self.failed - self.in_progress

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "in_progress": self.in_progress,
            "remaining": self.remaining,
            "percentage": self.percentage,
        }


async def process_with_rolling_window_progress(
    entities: List[T],
    process_fn: Callable[[T], Awaitable[R]],
    max_concurrent: int = 5,
    progress_callback: Callable[[RollingWindowProgress], None] = None
) -> List[R]:
    """
    Process entities with rolling window and progress tracking.

    Similar to process_with_rolling_window, but tracks progress and
    invokes a callback on progress updates.

    Args:
        entities: List of entities to process
        process_fn: Async function to process each entity
        max_concurrent: Maximum number of parallel operations
        progress_callback: Optional callback invoked on progress updates

    Returns:
        List of results from processing each entity

    Raises:
        Exception: If any processing task fails
    """
    if not entities:
        return []

    progress = RollingWindowProgress(total=len(entities))
    remaining = deque(entities)
    running = {}  # task -> entity
    results = []

    def notify_progress():
        """Notify progress callback if provided."""
        if progress_callback:
            progress_callback(progress)

    # Start initial batch
    while len(running) < max_concurrent and remaining:
        entity = remaining.popleft()
        task = asyncio.create_task(process_fn(entity))
        running[task] = entity

    progress.set_in_progress(len(running))
    notify_progress()

    # Process as they complete
    while running:
        done, pending = await asyncio.wait(
            running.keys(),
            return_when=asyncio.FIRST_COMPLETED
        )

        for completed_task in done:
            entity = running.pop(completed_task)

            # Get result
            try:
                result = completed_task.result()
                results.append(result)
                progress.increment_completed()
            except Exception as e:
                progress.increment_failed()
                # Re-raise with context
                raise Exception(f"Failed to process entity {entity}: {str(e)}") from e

            # Start next if available
            if remaining:
                next_entity = remaining.popleft()
                next_task = asyncio.create_task(process_fn(next_entity))
                running[next_task] = next_entity

        progress.set_in_progress(len(running))
        notify_progress()

    return results
