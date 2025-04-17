import logging

from fastapi import BackgroundTasks
from sqlmodel import select

from agroapp.bot_client import send_reactions
from agroapp.database import async_session
from agroapp.entities import ChatMessage, MessageStatus, Department, Operation, Crop
from agroapp.models import ChatMessageReactionRequest, MessageType
from agroapp.pipelines.message_definition import define_message_type
from agroapp.pipelines.report_solution import solve_reports

logger = logging.getLogger(__name__)


async def process_message(background_tasks: BackgroundTasks, chat_message_id: int) -> None:
    async with async_session() as session:
        result = await session.exec(select(ChatMessage).where(ChatMessage.id == chat_message_id))
        chat_message: ChatMessage = result.one_or_none()
        message_type = await define_message_type(chat_message.message_text)
        if message_type == MessageType.report:
            chat_message.status = MessageStatus.processing
            background_tasks.add_task(process_report, chat_message_id)
        else:
            chat_message.status = MessageStatus.spam
        await session.commit()
    await send_reactions(ChatMessageReactionRequest(
        chat_id=chat_message.chat_id,
        message_id=chat_message.message_id,
        status=chat_message.status,
    ))


async def process_report(chat_message_id: int):
    async with async_session() as session:
        chat_message: ChatMessage = (await session.exec(
            select(ChatMessage).where(ChatMessage.id == chat_message_id)
        )).one_or_none()
        try:
            departments: list[Department] = (await session.exec(select(Department))).all()
            operations: list[Operation] = (await session.exec(select(Operation))).all()
            crops: list[Crop] = (await session.exec(select(Crop))).all()
            reports = await solve_reports(
                message_id=chat_message.id,
                message_text=chat_message.message_text,
                message_created_at=chat_message.created_at,
                departments=departments,
                crops=crops,
                operations=operations,
            )
            session.add_all(reports)
            chat_message.status = MessageStatus.processed
            chat_message.status_text = f"Кол-во отчетов: {len(reports)}"
        except Exception as e:
            chat_message.status = MessageStatus.failed
            chat_message.status_text = str(e)
        await session.commit()
    await send_reactions(ChatMessageReactionRequest(
        chat_id=chat_message.chat_id,
        message_id=chat_message.message_id,
        status=chat_message.status,
    ))
