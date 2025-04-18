import logging
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException

from config import settings
from database import get_next_serial_num, async_session
from entities import ChatMessage
from models import ChatMessageCreateRequest, ChatMessageCreateResponse, MessageStatus
from processors import process_message

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
)


@router.post("/messages")
async def create_message(request: ChatMessageCreateRequest):
    try:
        logger.info(f"Received message: {request.message_text}")
        async with async_session() as session:
            chat_message = ChatMessage(**request.model_dump())
            chat_message.id = None
            chat_message.status = MessageStatus.new
            chat_message.created_at = request.created_at.astimezone(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)
            if settings.google_drive_folder_dumped:
                next_serial = await get_next_serial_num(session, request.user_id)
                chat_message.serial_num = next_serial
            else:
                chat_message.serial_num = 0
            session.add(chat_message)
            await session.commit()
            await session.refresh(chat_message)
        await process_message(chat_message.id)
        return ChatMessageCreateResponse(
            id=chat_message.id,
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
