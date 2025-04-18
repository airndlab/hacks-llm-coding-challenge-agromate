import base64
import io
import logging
import os
from typing import Optional

import aiohttp
import httpx
import yaml
from aiogram import Bot
from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReactionTypeEmoji
from openai import OpenAI

from app_client import create_message, create_report
from config import settings
from models import ChatMessageCreateRequest

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
llm_config = load_yaml_config('models.yaml')
llm_model = llm_config.get('ocr_model_name', 'gpt-4o')
audio_model = llm_config.get('audio_model_name', 'whisper-1')


def load_messages(path=settings.bot_messages_path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


msgs = load_messages()


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
                        {"type": "text", "text": OCR_SYSTEM_PROMPT},
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


# Загрузка голосового сообщения или аудио из сообщения
async def download_voice(message: Message) -> Optional[bytes]:
    content = message.voice or message.audio
    if not content:
        return None

    try:
        # Получаем URL файла
        file = await message.bot.get_file(content.file_id)

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
                        logger.error(f"Error downloading voice file: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error with aiohttp for voice: {e}")

            # Запасной вариант - используем httpx
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(file_url)
                    if response.status_code == 200:
                        return response.content
                    else:
                        logger.error(f"Error downloading voice file with httpx: HTTP {response.status_code}")
                        return None
            except Exception as e2:
                logger.error(f"Error with httpx for voice: {e2}")

                # Как последний вариант - используем встроенную функцию aiogram
                try:
                    return await message.bot.download_file(file.file_id)
                except Exception as e3:
                    logger.error(f"Error with aiogram download for voice: {e3}")
                    return None
    except Exception as e:
        logger.error(f"Error getting voice file information: {e}")
        return None


# Транскрибация голосового сообщения через OpenAI API
async def transcribe_audio(audio_bytes: bytes) -> str:
    try:
        # Сохраняем аудио во временный файл
        temp_file = io.BytesIO(audio_bytes)
        temp_file.name = "audio.ogg"  # Имя файла с расширением

        # Создаем клиент OpenAI с указанным API ключом
        client = OpenAI(api_key=settings.audio_api_key)

        # Вызываем API для транскрибации
        response = client.audio.transcriptions.create(
            model=audio_model,
            file=temp_file
        )

        return response.text
    except Exception as e:
        logger.error(f"Error in transcribe_audio: {e}", exc_info=True)
        return f"Ошибка при транскрибации аудио: {str(e)}"


# Обработка текста сообщения (и для обычных сообщений, и для распознанных из фото)
async def process_message_text(message: Message, text: str) -> None:
    if (message.forward_from and message.forward_from.username and message.forward_from.id):
        username = message.forward_from.username
        user_id = message.forward_from.id
    else:
        username = message.from_user.username
        user_id = message.from_user.id
    logger.info(f"Processing message from '{username}':\n{text}")
    created_message = await create_message(ChatMessageCreateRequest(
        username=str(username),
        user_id=str(user_id),
        chat_id=str(message.chat.id),
        message_id=str(message.message_id),
        message_text=text,
        created_at=message.date,
    ))
    logger.info(f"Created message from '{username}' with id: {created_message.id}")
    await message.react([ReactionTypeEmoji(emoji="🤔")])


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.reply(msgs["start"].format())


@dp.message(Command('report'))
async def command_report_handler(message: Message):
    await message.react([ReactionTypeEmoji(emoji="🤔")])
    report = await create_report()
    await message.reply((
        msgs["report"]
        .format(
            report_at=report.created_at.strftime('%d.%m.%Y %H:%M'),
            summary=report.summary,
            url=report.url,
        )
    ))
    await message.react([])


@dp.message(Command('schedule'))
async def command_schedule_handler(message: Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) == 2:
        time_arg = parts[1]
        await message.reply(msgs["schedule"]["success"].format(
            time=time_arg,
        ))
    else:
        await message.reply(msgs["schedule"]["error"].format())


@dp.message(Command('dashboard'))
async def command_dashboard_handler(message: Message):
    await message.reply(msgs["dashboard"].format(
        url=settings.dashboard_url
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


@dp.message(lambda message: message.voice or message.audio)
async def voice_handler(message: Message) -> None:
    try:
        username = message.from_user.username
        is_voice = bool(message.voice)
        content_type = "голосовое сообщение" if is_voice else "аудиофайл"

        logger.info(f"Received {content_type} from '{username}'")

        # Вывод информации о голосовом сообщении
        content = message.voice if is_voice else message.audio
        file_id = content.file_id
        duration = content.duration

        # Расширенное логирование информации о голосовом сообщении
        extra_info = {}
        if is_voice and hasattr(content, 'mime_type'):
            extra_info['mime_type'] = content.mime_type
        if hasattr(content, 'file_size'):
            extra_info['file_size'] = content.file_size

        logger.info(f"Voice/Audio message details: file_id={file_id}, duration={duration}s, extra_info={extra_info}")

        # Ответ пользователю о начале обработки
        processing_msg = await message.reply(f"Получил {content_type}! Длительность: {duration} сек. Обрабатываю...")

        # Загружаем аудио
        audio_bytes = await download_voice(message)
        if not audio_bytes:
            await processing_msg.edit_text(f"Не удалось загрузить {content_type}. Пожалуйста, попробуйте ещё раз.")
            return

        # Транскрибируем аудио
        transcribed_text = await transcribe_audio(audio_bytes)
        logger.info(f"Transcribed text from voice: {transcribed_text}")

        # Обновляем сообщение с результатом транскрибации
        await processing_msg.edit_text(f"Распознал следующий текст:\n\n{transcribed_text}\n\nОбрабатываю...")

        # Обрабатываем распознанный текст как обычное текстовое сообщение
        await process_message_text(message, transcribed_text)

        # Если есть подпись к голосовому сообщению
        caption = message.caption or ""
        if caption:
            logger.info(f"Voice/Audio caption: {caption}")
            await process_message_text(message, caption)

    except Exception as e:
        logger.error(f"Error in voice_handler: {e}", exc_info=True)
        await message.reply(f"Произошла ошибка при обработке голосового сообщения: {str(e)}")


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
