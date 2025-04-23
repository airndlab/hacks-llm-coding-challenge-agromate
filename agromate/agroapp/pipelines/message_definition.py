import logging
import os
import time
from pathlib import Path
from typing import Literal

import yaml
from config import settings
from jinja2 import Template
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from models import MessageType
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Загрузка конфигурации LLM и промптов
llm_config_path = os.path.join(settings.configs_path, "models.yaml")
prompts_config_path = os.path.join(settings.configs_path, "prompts.yaml")

with open(Path(llm_config_path), mode="r", encoding="utf-8") as f:
    llm_config = yaml.safe_load(f)

with open(Path(prompts_config_path), mode="r", encoding="utf-8") as f:
    prompts_config = yaml.safe_load(f)

# Загрузка шаблона системного промпта и примеров
SPAM_FILTER_SYSTEM_PROMPT_TEMPLATE = Template(prompts_config.get("spam_filter_system_prompt_template"))
spam_filter_few_shot_examples_str = prompts_config.get("spam_filter_few_shot_examples_str")

# Логирование информации о загрузке модуля
logger.info(f"Модуль message_definition загружен. Используется модель: {llm_config.get('model_name')}")
logger.info(f"Промпт и примеры загружены из {prompts_config_path}")


class MessageClassification(BaseModel):
    explanation: str = Field(
        ...,
        description="Short explanation in Russian why the message should or should not be processed."
    )
    message_type: Literal["field_report", "non_report"] = Field(
        ...,
        description="Message classification result: 'field_report' — if it's a pure fieldwork report, 'non_report' — if it's a question, discussion, planning, or irrelevant content."
    )


# Инициализация модели
model = ChatOpenAI(
    model=llm_config.get("llm_model_name"),
    openai_api_key=settings.llm_api_key,
    openai_api_base=settings.llm_api_base_url,
    temperature=llm_config.get("llm_temperature", 0.3),
    max_retries=30,
    timeout=90,
)


async def classify_message(
    message: str,
    model: ChatOpenAI,
) -> MessageClassification:
    """
    Классифицирует входящее сообщение на поле или спам
    
    Args:
        message: текст сообщения
        model: LLM модель для классификации
        
    Returns:
        MessageClassification: результат классификации
    """
    # Логирование входного сообщения (укороченная версия)
    message_preview = message[:150] + "..." if len(message) > 150 else message
    logger.info(f"Начало классификации сообщения: '{message_preview.replace(chr(10), ' ')}'")
    
    start_time = time.time()
    
    system_prompt = SPAM_FILTER_SYSTEM_PROMPT_TEMPLATE.render(
        json_schema=MessageClassification.model_json_schema(),
        few_shot_examples=spam_filter_few_shot_examples_str,
        message=message,
    )

    logger.info(f"Отправка запроса к модели {llm_config.get('llm_model_name')}")
    
    try:
        answer = await model.with_structured_output(MessageClassification).ainvoke(
            [SystemMessage(content=system_prompt)]
        )
        
        # Логирование результата классификации
        execution_time = time.time() - start_time
        logger.info(f"Результат классификации: {answer.message_type} [время: {execution_time:.2f}с]")
        logger.info(f"Объяснение: {answer.explanation}")
        
        return answer
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Ошибка при классификации сообщения: {e} [время: {execution_time:.2f}с]", exc_info=True)
        raise


async def define_message_type(text: str) -> MessageType:
    """
    Определяет тип сообщения: отчет, загрузка или спам
    
    Args:
        text: текст сообщения
        
    Returns:
        MessageType: тип сообщения
    """
    # Логирование вызова функции
    message_len = len(text)
    logger.info(f"Определение типа сообщения длиной {message_len} символов")
    
    try:
        # Классификация сообщения через LLM
        result = await classify_message(text, model)
        
        # Преобразование результата классификации в MessageType
        if result.message_type == "field_report":
            logger.info(f"Сообщение определено как отчет о полевых работах: {MessageType.report}")
            return MessageType.report
        else:
            logger.info(f"Сообщение определено как спам или не полевой отчет: {MessageType.spam}")
            return MessageType.spam
            
    except Exception as e:
        # В случае ошибки считаем сообщение отчетом для последующей обработки
        # Это предотвращает потерю потенциально важных данных
        logger.error(f"Ошибка при определении типа сообщения: {e}", exc_info=True)
        logger.warning(f"Из-за ошибки сообщение будет обработано как отчет: {MessageType.report}")
        return MessageType.report
