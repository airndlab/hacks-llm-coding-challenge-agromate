import asyncio
import logging

from sqlalchemy.orm import selectinload
from sqlmodel import select

from bg import run_safe
from bot_client import send_reactions, reply_on_message
from config import settings
from database import async_session
from dump import dump_message_silently, dump_report_silently
from entities import ChatMessage, MessageStatus, Department, Operation, Crop, Report
from models import ChatMessageReactionRequest, MessageType, ChatMessageReplyRequest
from pipelines.message_definition import define_message_type
from pipelines.report_solution import solve_reports

logger = logging.getLogger(__name__)


async def process_message(chat_message_id: int) -> None:
    async with async_session() as session:
        result = await session.exec(select(ChatMessage).where(ChatMessage.id == chat_message_id))
        chat_message: ChatMessage = result.one_or_none()
        message_type = await define_message_type(chat_message.message_text)
        if message_type == MessageType.report:
            chat_message.status = MessageStatus.processing
            if settings.google_drive_folder_dumped:
                dump_message_silently(chat_message)
            asyncio.create_task(run_safe(process_report, chat_message_id))
        else:
            chat_message.status = MessageStatus.spam
        await session.commit()
    if chat_message.status == MessageStatus.spam:
        try:
            await send_reactions(ChatMessageReactionRequest(
                chat_id=chat_message.chat_id,
                message_id=chat_message.message_id,
                status=chat_message.status,
            ))
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)


async def process_report(chat_message_id: int):
    async with async_session() as session:
        chat_message: ChatMessage = (await session.exec(
            select(ChatMessage).where(ChatMessage.id == chat_message_id)
        )).one_or_none()
        try:
            departments: list[Department] = (await session.exec(select(Department))).all()
            operations: list[Operation] = (await session.exec(select(Operation))).all()
            crops: list[Crop] = (await session.exec(select(Crop))).all()
            created_reports = await solve_reports(
                message_id=chat_message.id,
                message_text=chat_message.message_text,
                message_created_at=chat_message.created_at,
                departments=departments,
                crops=crops,
                operations=operations,
            )
            session.add_all(created_reports)
            chat_message.status = MessageStatus.processed
            chat_message.status_text = f"Кол-во отчетов: {len(created_reports)}"
            if settings.google_drive_folder_dumped:
                await session.flush()
                created_ids = [r.id for r in created_reports]
                reports: list[Report] = (await session.exec(
                    select(Report)
                    .options(
                        selectinload(Report.department),
                        selectinload(Report.operation),
                        selectinload(Report.crop)
                    )
                    .where(Report.id.in_(created_ids))
                )).all()
                dump_report_silently(chat_message, reports)
        except Exception as e:
            chat_message.status = MessageStatus.failed
            chat_message.status_text = str(e)
            logger.error(f"Error: {e}", exc_info=True)
        await session.commit()
    try:
        await send_reactions(ChatMessageReactionRequest(
            chat_id=chat_message.chat_id,
            message_id=chat_message.message_id,
            status=chat_message.status,
        ))
        if settings.bot_reply_on_failed and chat_message.status == MessageStatus.failed:
            await reply_on_message(ChatMessageReplyRequest(
                chat_id=chat_message.chat_id,
                message_id=chat_message.message_id,
                text=(
                    f"🌾 Нашла коса на камень..."
                    f"\n\n"
                    f"Что-то пошло не так при обработке отчёта."
                    f"\n\n"
                    f"{chat_message.status_text}"
                )
            ))
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
