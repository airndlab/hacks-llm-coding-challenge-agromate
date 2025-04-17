import logging

from fastapi import BackgroundTasks
from sqlalchemy.orm import selectinload
from sqlmodel import select

from bot_client import send_reactions, reply_on_message
from config import settings
from database import async_session
from dump import dump_message_silently, dump_report_silently
from entities import ChatMessage, MessageStatus, Department, Operation, Crop, Report
from google_drive import upload_excel_file_to_folder
from models import ChatMessageReactionRequest, MessageType, ChatMessageReplyRequest
from pipelines.message_definition import define_message_type
from pipelines.report_solution import solve_reports
from report import create_excel_report_file

logger = logging.getLogger(__name__)


async def process_message(background_tasks: BackgroundTasks, chat_message_id: int) -> None:
    async with async_session() as session:
        result = await session.exec(select(ChatMessage).where(ChatMessage.id == chat_message_id))
        chat_message: ChatMessage = result.one_or_none()
        message_type = await define_message_type(chat_message.message_text)
        if message_type == MessageType.report:
            chat_message.status = MessageStatus.processing
            if settings.google_drive_folder_dumped:
                dump_message_silently(chat_message)
            background_tasks.add_task(process_report, chat_message_id)
        elif message_type == MessageType.upload:
            chat_message.status = MessageStatus.spam
            background_tasks.add_task(upload_report, chat_message_id)
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
            if settings.google_drive_folder_dumped:
                dump_report_silently(chat_message, reports)
        except Exception as e:
            chat_message.status = MessageStatus.failed
            chat_message.status_text = str(e)
            logger.error("Error: {e}", exc_info=True)
        await session.commit()
    try:
        await send_reactions(ChatMessageReactionRequest(
            chat_id=chat_message.chat_id,
            message_id=chat_message.message_id,
            status=chat_message.status,
        ))
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


async def upload_report(chat_message_id: int):
    async with async_session() as session:
        chat_message: ChatMessage = (await session.exec(
            select(ChatMessage).where(ChatMessage.id == chat_message_id)
        )).one_or_none()
        report_on = chat_message.created_at.date()
        reports: list[Report] = (await session.exec(
            select(Report)
            .options(
                selectinload(Report.department),
                selectinload(Report.operation),
                selectinload(Report.crop)
            )
            .where(Report.worked_on == report_on)
        )).all()
        file_path = create_excel_report_file(report_on, reports)
        _, file_url = upload_excel_file_to_folder(file_path)
        await session.commit()
    try:
        await reply_on_message(ChatMessageReplyRequest(
            chat_id=chat_message.chat_id,
            message_id=chat_message.message_id,
            text=f"Выгружен отчет на {report_on.strftime('%d-%m-%Y')}:\n{file_url}"
        ))
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
