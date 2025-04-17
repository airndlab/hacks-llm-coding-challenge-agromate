import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.types import Message, ReactionTypeEmoji

from agrobot.app_client import create_message
from agrobot.models import ChatMessageCreateRequest

logger = logging.getLogger(__name__)

dp = Dispatcher()


@dp.message()
async def question_handler(message: Message) -> None:
    try:
        username = message.from_user.username
        message_text = message.text
        logger.info(f"Received message from '{username}':\n{message_text}")
        created_message = await create_message(ChatMessageCreateRequest(
            username=str(message.from_user.username),
            user_id=str(message.from_user.id),
            chat_id=str(message.chat.id),
            message_id=str(message.message_id),
            message_text=message_text,
            created_at=message.date,
        ))
        logger.info(f"Created message from '{username}' with id: {created_message.id}")
        await message.react([ReactionTypeEmoji(emoji="👀")])
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await message.react([ReactionTypeEmoji(emoji="🗿")])


async def start_pooling(bot: Bot) -> None:
    await dp.start_polling(bot)
