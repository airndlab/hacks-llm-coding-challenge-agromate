import logging

import uvicorn
from aiogram.types import ReactionTypeEmoji
from fastapi import FastAPI, HTTPException

from agrobot.bot import bot_client
from agrobot.config import settings
from agrobot.models import ChatMessageReactionRequest, MessageStatus

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


@app.post("/api/sending/reactions")
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
    config = uvicorn.Config(app, host="localhost", port=8088, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()
