import logging
import io
import base64
import os
import yaml
from typing import Optional
import httpx
import aiohttp
import asyncio

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, ReactionTypeEmoji
from aiogram.enums.content_type import ContentType
from openai import OpenAI
from PIL import Image

from app_client import create_message
from models import ChatMessageCreateRequest
from config import settings

logger = logging.getLogger(__name__)

dp = Dispatcher()

# Загрузка конфигурационных файлов
def load_yaml_config(filename):
    config_path = os.path.join(settings.bot_configs_path, filename)
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации {filename}: {e}")
        return {}

# Загрузка промптов
prompts_config = load_yaml_config('prompts.yaml')
OCR_SYSTEM_PROMPT = prompts_config.get('ocr_system_prompt', '')

# Загрузка конфигурации LLM
llm_config = load_yaml_config('llm.yaml')
llm_model = llm_config.get('model', 'gpt-4o')

# Кодирование изображения в base64
def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

# Вызов OpenAI Vision API
async def transcribe_image(base64_image: str) -> str:
    try:
        client = OpenAI(api_key=settings.ocr_api_key)
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        { "type": "text", "text": OCR_SYSTEM_PROMPT },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in transcribe_image: {e}", exc_info=True)
        return f"Ошибка при распознавании изображения: {str(e)}"

# Загрузка изображения из сообщения
async def download_photo(message: Message) -> Optional[bytes]:
    if not message.photo:
        return None
    
    # Получаем фото наилучшего качества (последний элемент в списке)
    photo = message.photo[-1]
    
    try:
        # Получаем URL файла
        file = await message.bot.get_file(photo.file_id)
        
        # Формируем URL для скачивания
        file_path = file.file_path
        bot_token = settings.bot_token
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        
        # Скачиваем файл через aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Error downloading file: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error with aiohttp: {e}")
            
            # Запасной вариант - используем httpx
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(file_url)
                    if response.status_code == 200:
                        return response.content
                    else:
                        logger.error(f"Error downloading file with httpx: HTTP {response.status_code}")
                        return None
            except Exception as e2:
                logger.error(f"Error with httpx: {e2}")
                
                # Как последний вариант - используем встроенную функцию aiogram
                try:
                    return await message.bot.download_file(file.file_id)
                except Exception as e3:
                    logger.error(f"Error with aiogram download: {e3}")
                    return None
    except Exception as e:
        logger.error(f"Error getting file information: {e}")
        return None

# Обработка текста сообщения (и для обычных сообщений, и для распознанных из фото)
async def process_message_text(message: Message, text: str) -> None:
    username = message.from_user.username
    logger.info(f"Processing message from '{username}':\n{text}")
    
    created_message = await create_message(ChatMessageCreateRequest(
        username=str(message.from_user.username),
        user_id=str(message.from_user.id),
        chat_id=str(message.chat.id),
        message_id=str(message.message_id),
        message_text=text,
        created_at=message.date,
    ))
    
    logger.info(f"Created message from '{username}' with id: {created_message.id}")
    await message.react([ReactionTypeEmoji(emoji="🤔")])


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


@dp.message(lambda message: message.photo)
async def photo_handler(message: Message) -> None:
    try:
        username = message.from_user.username
        logger.info(f"Received photo from '{username}'")
        
        # Реагируем на сообщение и сообщаем о начале обработки
        await message.react([ReactionTypeEmoji(emoji="👍")])
        processing_msg = await message.reply("Получил фотографию! Обрабатываю...")
        
        # Загружаем фото
        photo_bytes = await download_photo(message)
        if not photo_bytes:
            await processing_msg.edit_text("Не удалось загрузить фото. Пожалуйста, попробуйте ещё раз.")
            return
        
        # Получаем подпись к фото, если есть
        caption = message.caption or ""
        if caption:
            logger.info(f"Photo caption: {caption}")
            await process_message_text(message, caption)
            await processing_msg.edit_text(f"Обработал подпись к фото: {caption}")
            return
        
        # Кодируем фото в base64
        base64_image = encode_image(photo_bytes)
        
        # Распознаем текст с изображения
        recognized_text = await transcribe_image(base64_image)
        logger.info(f"Recognized text from photo: {recognized_text}")
        
        # Редактируем сообщение об обработке, показывая распознанный текст
        await processing_msg.edit_text(f"Распознал следующий текст:\n\n{recognized_text}\n\nОбрабатываю...")
        
        # Обрабатываем распознанный текст как обычное сообщение
        await process_message_text(message, recognized_text)
        
    except Exception as e:
        logger.error(f"Error in photo_handler: {e}", exc_info=True)
        await message.reply(f"Произошла ошибка при обработке фотографии: {str(e)}")
        await message.react([ReactionTypeEmoji(emoji="😢")])


@dp.message()
async def question_handler(message: Message) -> None:
    try:
        message_text = message.text
        await process_message_text(message, message_text)
    except Exception as e:
        logger.error(f"Error in question_handler: {e}", exc_info=True)
        await message.react([ReactionTypeEmoji(emoji="😢")])


async def start_pooling(bot: Bot) -> None:
    await dp.start_polling(bot)
