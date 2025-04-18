import asyncio
import logging

logger = logging.getLogger(__name__)
semaphore = asyncio.Semaphore(20)


async def run_safe(task_fn, *args, **kwargs):
    async with semaphore:
        try:
            await task_fn(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Task {task_fn.__name__} failed with: {e}")
