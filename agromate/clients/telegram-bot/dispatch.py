import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, ReactionTypeEmoji

from app_client import create_message
from models import ChatMessageCreateRequest

logger = logging.getLogger(__name__)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.reply((
        f"🌾 Привет, коллега!"
        f"\n\n"
        f"Я — твой цифровой помощник в поле бумажек. Помогаю с бюрократическим урожаем таким как отчёты."
        f"\n"
        f"Кидай сюда данные по операциям — посев, обработка, подкормка, что угодно — я всё упакую как надо."
        f"\n\n"
        f"📋 Чтобы начать — просто напиши сообщение с деталями работы."
        f"\n"
        f"✍️ Например: * «17.04 юг, дисковка, подсолнечник, 45 га» *"
        f"\n\n"
        f"Если запутаешься — не страшно, я рядом."
        f"\n"
        f"А если совсем всё плохо — зови на помощь /help."
        f"\n\n"
        f"Ну что, поехали? 🚜"
    ))


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
        await message.react([ReactionTypeEmoji(emoji="🤔")])
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await message.react([ReactionTypeEmoji(emoji="🗿")])


async def start_pooling(bot: Bot) -> None:
    await dp.start_polling(bot)
