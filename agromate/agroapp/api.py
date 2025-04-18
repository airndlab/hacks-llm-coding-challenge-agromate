import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from bg import run_safe
from config import settings
from database import get_async_session_as_generator, get_next_serial_num
from entities import ChatMessage, Report
from google_drive import upload_excel_file_to_folder
from models import ChatMessageCreateRequest, ChatMessageCreateResponse, MessageStatus, ReportResponse
from processors import process_message
from report import create_excel_report_file

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
)

tz = ZoneInfo("Europe/Moscow")


@router.post("/messages")
async def create_message(
        request: ChatMessageCreateRequest,
        session: AsyncSession = Depends(get_async_session_as_generator),
):
    try:
        logger.info(f"Received message: {request.message_text}")
        chat_message = ChatMessage(**request.model_dump())
        chat_message.id = None
        chat_message.status = MessageStatus.new
        chat_message.created_at = request.created_at.astimezone(tz).replace(tzinfo=None)
        if settings.google_drive_folder_dumped:
            next_serial = await get_next_serial_num(session, request.user_id)
            chat_message.serial_num = next_serial
        else:
            chat_message.serial_num = 0
        session.add(chat_message)
        await session.commit()
        await session.refresh(chat_message)
        asyncio.create_task(run_safe(process_message, chat_message.id))
        return ChatMessageCreateResponse(
            id=chat_message.id,
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/reports")
async def create_report(session: AsyncSession = Depends(get_async_session_as_generator)):
    report_at = datetime.now(tz)
    reports: list[Report] = (await session.exec(
        select(Report)
        .options(
            selectinload(Report.department),
            selectinload(Report.operation),
            selectinload(Report.crop)
        )
        .where(Report.worked_on == report_at)
    )).all()
    file_path = create_excel_report_file(report_at, reports)
    _, file_url = upload_excel_file_to_folder(file_path)
    # TODO: add pipeline
    summary = f'Даже не знаю с чего начать...'
    return ReportResponse(
        created_at=report_at,
        url=file_url,
        summary=summary
    )
