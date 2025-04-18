import csv
import logging
import os
from typing import AsyncGenerator, Any

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from config import settings
from entities import Department, Operation, Crop, ChatMessage

logger = logging.getLogger(__name__)

async_engine = create_async_engine(
    settings.db_url,
    echo=True,
    future=True,
)

async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_session_as_generator() -> AsyncGenerator[AsyncSession, Any]:
    async with async_session() as session:
        yield session


def load_csv_as_dicts(csv_path: str) -> list[dict]:
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return []
    with open(csv_path, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


async def load_dicts():
    async with async_session() as session:
        result = await session.exec(select(Department))
        departments = result.all()
        if not departments:
            csv_path = f"{settings.dicts_path}/departments.csv"
            logger.info(f"Loading departments from CSV: {csv_path}")
            dept_data = load_csv_as_dicts(csv_path)
            dept_objs = [Department(**row) for row in dept_data]
            session.add_all(dept_objs)
        else:
            logger.info("Departments already present in DB")

        result = await session.exec(select(Operation))
        operations = result.all()
        if not operations:
            csv_path = f"{settings.dicts_path}/operations.csv"
            logger.info(f"Loading operations from CSV: {csv_path}")
            op_data = load_csv_as_dicts(csv_path)
            op_objs = [Operation(**row) for row in op_data]
            session.add_all(op_objs)
        else:
            logger.info("Operations already present in DB")

        result = await session.exec(select(Crop))
        crops = result.all()
        if not crops:
            csv_path = f"{settings.dicts_path}/crops.csv"
            logger.info(f"Loading crops from CSV: {csv_path}")
            crop_data = load_csv_as_dicts(csv_path)
            crop_objs = [Crop(**row) for row in crop_data]
            session.add_all(crop_objs)
        else:
            logger.info("Crops already present in DB")

        await session.commit()


async def get_next_serial_num(session: AsyncSession, user_id: str) -> int:
    # Хешируем user_id в int64 (можно заменить на crc32, если хочешь стабильность между перезапусками)
    lock_key = abs(hash(user_id)) % (2 ** 31)

    await session.execute(text(f"SELECT pg_advisory_xact_lock({lock_key})"))

    result = await session.exec(
        select(func.coalesce(func.max(ChatMessage.serial_num), 0))
        .where(ChatMessage.user_id == user_id)
    )
    return result.one() + 1
