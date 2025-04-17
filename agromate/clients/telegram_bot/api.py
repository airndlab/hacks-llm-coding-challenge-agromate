import logging

import uvicorn
from aiogram.types import ReactionTypeEmoji
from fastapi import FastAPI, HTTPException

from agrobot.bot import bot_client
from agrobot.config import settings
from agrobot.models import ChatMessageReactionRequest, MessageStatus, ChatMessageReplyRequest

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgroMate Bot API",
    description="""
    AgroMate Bot
    """,
    version="0.1.0",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 3,
        "deepLinking": True
    },
    debug=settings.debug,
)


@app.get("/")
async def status():
    return {"status": "UP"}


@app.post("/api/replies")
async def reply_on_message(request: ChatMessageReplyRequest):
    try:
        await bot_client.send_message(
            chat_id=request.chat_id,
            reply_to_message_id=request.message_id,
            text=request.text,
        )
        logger.info(f"Replied on message '{request.chat_id}:{request.message_id}' with text: {request.text}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/reactions")
async def set_reaction_on_status(request: ChatMessageReactionRequest):
    try:
        if request.status == MessageStatus.spam:
            reaction = []
        elif request.status == MessageStatus.processing:
            reaction = [ReactionTypeEmoji(emoji="🤔")]
        elif request.status == MessageStatus.processed:
            reaction = [ReactionTypeEmoji(emoji="👌")]
        elif request.status == MessageStatus.failed:
            reaction = [ReactionTypeEmoji(emoji="😢")]
        else:
            reaction = [ReactionTypeEmoji(emoji="🤷")]
        await bot_client.set_message_reaction(
            chat_id=request.chat_id,
            message_id=request.message_id,
            reaction=reaction
        )
        logger.info(f"Set reaction on status '{request.status}' for message: {request.chat_id}:{request.message_id}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


async def start_api():
    config = uvicorn.Config("agrobot.api:app", host="0.0.0.0", port=8088, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()
