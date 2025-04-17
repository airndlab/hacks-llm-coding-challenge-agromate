import logging

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from agroapp.processors import process_message
from agroapp.database import get_async_session_as_generator
from agroapp.entities import ChatMessage
from agroapp.models import ChatMessageCreateRequest, ChatMessageCreateResponse, MessageStatus

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
)


@router.post("/messages")
async def create_message(
        request: ChatMessageCreateRequest,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session_as_generator),
):
    try:
        logger.info(f"Received message: {request.message_text}")
        chat_message = ChatMessage(**request.model_dump())
        chat_message.id = None
        chat_message.status = MessageStatus.new
        chat_message.created_at = chat_message.created_at.replace(tzinfo=None)
        session.add(chat_message)
        await session.commit()
        await session.refresh(chat_message)
        background_tasks.add_task(process_message, background_tasks, chat_message.id)
        return ChatMessageCreateResponse(
            id=chat_message.id,
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
