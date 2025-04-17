import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import init_db, load_dicts

logger = logging.getLogger(__name__)


@asynccontextmanager
async def life_hook(app: FastAPI):
    logger.info('Startup hook')
    await init_db()
    await load_dicts()
    yield
    logger.info('Shutdown hook')
