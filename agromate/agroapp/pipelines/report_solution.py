import os
from datetime import datetime
from pathlib import Path
import yaml
import time

from .utils import (
    extract_department_names,
    generate_field_work_log_schema,
    _match_department_id,
    _match_crop_id,
    _match_operation_id,
    create_annotated_field_work_log_schema,
)

from config import settings
from entities import Report, Department, Operation, Crop

from jinja2 import Template

from langchain_openai import ChatOpenAI

from langchain_core.messages import SystemMessage

import logging

logger = logging.getLogger(__name__)

# Получаем режим работы пайплайна из переменной окружения
# Возможные значения: AUTO (по умолчанию) или DEMO
MODE = settings.mode
logger.info(f"🚀 Запуск пайплайна report_solution в режиме: {MODE}")

# Загружаем конфигурацию
llm_config_path = os.path.join(settings.configs_path, "models.yaml")
prompts_config_path = os.path.join(settings.configs_path, "prompts.yaml")

with open(Path(llm_config_path), mode="r", encoding="utf-8") as f:
    llm_config = yaml.safe_load(f)

with open(Path(prompts_config_path), mode="r", encoding="utf-8") as f:
    prompts_config = yaml.safe_load(f)

# Шаблоны и подсказки для режима AUTO
AUTO_SYSTEM_PROMPT_TEMPLATE = Template(prompts_config.get("baseline_system_prompt_template"))
auto_schema_hints = prompts_config.get("baseline_schema_hints")
auto_few_shot_examples_str = prompts_config.get("baseline_few_shot_examples_str")

# Шаблоны и подсказки для режима DEMO
DEMO_SYSTEM_PROMPT_TEMPLATE = Template(prompts_config.get("mode_demo_system_prompt_template"))
demo_schema_hints = prompts_config.get("demo_mode_schema_hints")
demo_few_shot_examples_str = prompts_config.get("demo_mode_few_shot_examples_str",)

# Инициализируем модель
model = ChatOpenAI(
    model=llm_config.get("llm_model_name"),
    openai_api_key=settings.llm_api_key,
    openai_api_base=settings.llm_api_base_url,
    temperature=llm_config.get("llm_temperature", 0.3),
    max_retries=30,
    timeout=90,
)
logger.info(f"🤖 Инициализирована модель: {llm_config.get('llm_model_name')}")


async def solve_reports(
        message_id: int,
        message_text: str,
        message_created_at: datetime,
        departments: list[Department],
        crops: list[Crop],
        operations: list[Operation],
) -> list[Report]:
    start_time = time.time()
    logger.info(f"⏳ Начинается обработка сообщения ID: {message_id}")
    logger.info(f"   Длина текста: {len(message_text)} символов")
    logger.info(f"   Первые 100 символов: {message_text[:100].replace(chr(10), ' ')}...")
    logger.info(f"   Дата создания: {message_created_at}")

    # Извлекаем имена для Literal-типов
    department_names = extract_department_names(departments)
    logger.info(f"   Доступные подразделения: {department_names}")
    crop_names = tuple(crop.crop_name for crop in crops)
    logger.info(f"   Доступные культуры: {crop_names}")
    operation_names = tuple(op.operation_name for op in operations)
    logger.info(f"   Доступные операции: {operation_names}")

    logger.info(f"📊 Доступные сущности в БД:")
    logger.info(f"   Подразделения: {len(departments)} (в ПУ: {len(department_names)})")
    logger.info(f"   Культуры: {len(crops)}")
    logger.info(f"   Операции: {len(operations)}")

    # Подготовка данных в зависимости от выбранного режима
    if MODE == "DEMO":
        logger.info(f"🔄 Используется режим DEMO с аннотированными полями")
        try:
            # Генерируем схему с аннотированными полями для режима DEMO
            FieldWorkEntryAnnotated, FieldWorkLogAnnotated = create_annotated_field_work_log_schema(
                department_names=department_names,
                operations=operation_names,
                crops=crop_names,
            )
            
            # Создаем промпт для режима DEMO
            system_prompt = DEMO_SYSTEM_PROMPT_TEMPLATE.render(
                json_schema=FieldWorkLogAnnotated.model_json_schema(),
                few_shot_examples=demo_few_shot_examples_str,
                message=message_text,
                schema_hints=demo_schema_hints,
            )
            
            # Выполняем запрос к модели
            logger.info(f"🧠 Отправка запроса к модели {llm_config.get('llm_model_name')}")
            model_start_time = time.time()
            field_work_log = await model.with_structured_output(FieldWorkLogAnnotated).ainvoke(
                [SystemMessage(content=system_prompt)]
            )
            model_end_time = time.time()
            logger.info(f"✅ Ответ от модели получен. Время выполнения: {model_end_time - model_start_time:.2f} сек.")
            logger.info(f"📝 Выделено записей: {len(field_work_log.entries)}")
            
            # Добавляем детальное логирование выделенных записей
            for i, entry in enumerate(field_work_log.entries):
                logger.info(f"  📄 Запись #{i+1}:")
                
                dept_status = entry.department_name.status
                dept_value = entry.department_name.value
                logger.info(f"    🏢 Подразделение: [{dept_status}] {dept_value}")
                if dept_status != 'valid':
                    if hasattr(entry.department_name, 'explanation'):
                        logger.info(f"       📝 Объяснение: {entry.department_name.explanation}")
                
                op_status = entry.operation.status
                op_value = entry.operation.value
                logger.info(f"    🔨 Операция: [{op_status}] {op_value}")
                if op_status != 'valid':
                    if hasattr(entry.operation, 'explanation'):
                        logger.info(f"       📝 Объяснение: {entry.operation.explanation}")
                
                crop_status = entry.crop.status
                crop_value = entry.crop.value
                logger.info(f"    🌱 Культура: [{crop_status}] {crop_value}")
                if crop_status != 'valid':
                    if hasattr(entry.crop, 'explanation'):
                        logger.info(f"       📝 Объяснение: {entry.crop.explanation}")
                
                logger.info(f"    📊 Площадь день/всего: {entry.processed_area_day}/{entry.processed_area_total} га")
                if entry.yield_kg_day or entry.yield_kg_total:
                    logger.info(f"    📈 Урожай день/всего: {entry.yield_kg_day or 'Нет'}/{entry.yield_kg_total or 'Нет'} кг")
            
            # Обрабатываем результат
            reports = []
            for entry in field_work_log.entries:
                # Получаем значения и обрабатываем аннотации
                department_id = None
                department_raw = None
                department_predicted = None
                
                # Собираем все объяснения для поля note
                explanations = []
                
                if entry.department_name.status == 'valid':
                    try:
                        department_id = _match_department_id(entry.department_name.value, departments)
                        logger.info(f"   💼 Подразделение '{entry.department_name.value}' определено как valid, ID: {department_id}")
                    except ValueError as e:
                        # Если не найдено соответствие, обрабатываем как raw
                        logger.warning(f"   ⚠️ Подразделение '{entry.department_name.value}' помечено как valid, но не найдено в БД")
                        department_raw = entry.department_name.value
                        department_predicted = entry.department_name.value
                        explanations.append(f"Подразделение: {str(e)}")
                elif entry.department_name.status == 'predict':
                    department_raw = None
                    department_predicted = entry.department_name.value
                    explanations.append(f"Подразделение: {entry.department_name.explanation}")
                    logger.info(f"   🔍 Подразделение '{entry.department_name.value}' определено как predict: {entry.department_name.explanation}")
                else:  # 'raw'
                    department_raw = entry.department_name.value
                    department_predicted = None
                    explanations.append(f"Подразделение: {entry.department_name.explanation}")
                    logger.info(f"   ⚠️ Подразделение '{department_raw}' определено как raw с объяснением: {entry.department_name.explanation}")
                
                operation_id = None
                operation_raw = None
                operation_predicted = None
                
                if entry.operation.status == 'valid':
                    try:
                        operation_id = _match_operation_id(entry.operation.value, operations)
                        logger.info(f"   💼 Операция '{entry.operation.value}' определена как valid, ID: {operation_id}")
                    except ValueError as e:
                        # Если не найдено соответствие, обрабатываем как raw
                        logger.warning(f"   ⚠️ Операция '{entry.operation.value}' помечена как valid, но не найдена в БД")
                        operation_raw = entry.operation.value
                        operation_predicted = entry.operation.value
                        explanations.append(f"Операция: {str(e)}")
                elif entry.operation.status == 'predict':
                    operation_raw = None
                    operation_predicted = entry.operation.value
                    explanations.append(f"Операция: {entry.operation.explanation}")
                    logger.info(f"   🔍 Операция '{entry.operation.value}' определена как predict: {entry.operation.explanation}")
                else:  # 'raw'
                    operation_raw = entry.operation.value
                    operation_predicted = None
                    explanations.append(f"Операция: {entry.operation.explanation}")
                    logger.info(f"   ⚠️ Операция '{operation_raw}' определена как raw с объяснением: {entry.operation.explanation}")
                
                crop_id = None
                crop_raw = None
                crop_predicted = None
                
                if entry.crop.status == 'valid':
                    try:
                        crop_id = _match_crop_id(entry.crop.value, crops)
                        logger.info(f"   💼 Культура '{entry.crop.value}' определена как valid, ID: {crop_id}")
                    except ValueError as e:
                        # Если не найдено соответствие, обрабатываем как raw
                        logger.warning(f"   ⚠️ Культура '{entry.crop.value}' помечена как valid, но не найдена в БД")
                        crop_raw = entry.crop.value
                        crop_predicted = entry.crop.value
                        explanations.append(f"Культура: {str(e)}")
                elif entry.crop.status == 'predict':
                    crop_raw = None
                    crop_predicted = entry.crop.value
                    explanations.append(f"Культура: {entry.crop.explanation}")
                    logger.info(f"   🔍 Культура '{entry.crop.value}' определена как predict: {entry.crop.explanation}")
                else:  # 'raw'
                    crop_raw = entry.crop.value
                    crop_predicted = None
                    explanations.append(f"Культура: {entry.crop.explanation}")
                    logger.info(f"   ⚠️ Культура '{crop_raw}' определена как raw с объяснением: {entry.crop.explanation}")
                
                # Создаем note объединением всех объяснений
                note = None
                if explanations:
                    note = "; ".join(explanations)
                    logger.info(f"   📝 Создана заметка: {note}")
                
                # Проверяем, что хотя бы один из ID не None
                if department_id is None and operation_id is None and crop_id is None:
                    logger.warning(f"   ⚠️ Ни одно поле не имеет валидного ID, используем заглушки из первых записей")
                    # Используем первые записи в качестве заглушек, если ни один ID не найден
                    if not department_id and departments:
                        department_id = departments[0].id
                        logger.info(f"   🔧 Установлена заглушка для department_id: {department_id}")
                    if not operation_id and operations:
                        operation_id = operations[0].id
                        logger.info(f"   🔧 Установлена заглушка для operation_id: {operation_id}")
                    if not crop_id and crops:
                        crop_id = crops[0].id
                        logger.info(f"   🔧 Установлена заглушка для crop_id: {crop_id}")
                
                # Преобразование килограммов в центнеры (делим на 100)
                day_yield = None
                cumulative_yield = None
                
                if entry.yield_kg_day is not None:
                    day_yield = entry.yield_kg_day / 100
                    logger.info(f"   📊 Конвертация день, кг -> цн: {entry.yield_kg_day} -> {day_yield}")
                    
                if entry.yield_kg_total is not None:
                    cumulative_yield = entry.yield_kg_total / 100
                    logger.info(f"   📊 Конвертация всего, кг -> цн: {entry.yield_kg_total} -> {cumulative_yield}")
                
                # Проверяем только day_area, так как это обязательное поле
                day_area = entry.processed_area_day
                if day_area is None or day_area <= 0:
                    day_area = 1
                    logger.warning(f"   ⚠️ Некорректное значение day_area: {entry.processed_area_day}, устанавливаем значение 1")
                
                # Сохраняем cumulative_area как None, если модель вернула processed_area_total = None
                cumulative_area = entry.processed_area_total
                
                # Создаем объект Report с учетом аннотаций
                report = Report(
                    worked_on=message_created_at.date(),
                    chat_message_id=message_id,
                    department_id=department_id,
                    operation_id=operation_id,
                    crop_id=crop_id,
                    department_raw=department_raw,
                    operation_raw=operation_raw,
                    crop_raw=crop_raw,
                    department_predicted=department_predicted,
                    operation_predicted=operation_predicted,
                    crop_predicted=crop_predicted,
                    note=note,
                    day_area=day_area,
                    cumulative_area=cumulative_area,
                    day_yield=day_yield,
                    cumulative_yield=cumulative_yield,
                )
                logger.info(f"   ✅ Объект Report создан")
                reports.append(report)
                
            logger.info(f"   ✅ Создано записей Report: {len(reports)}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в режиме DEMO: {e}", exc_info=True)
            raise
    else:
        # Стандартный режим AUTO
        logger.info(f"🔄 Используется стандартный режим AUTO")
        try:
            # Генерируем стандартную Pydantic-схему
            FieldWorkLog = generate_field_work_log_schema(
                department_names=department_names,
                operations=operation_names,
                crops=crop_names,
            )
            
            # Создаем промпт для режима AUTO
            system_prompt = AUTO_SYSTEM_PROMPT_TEMPLATE.render(
                json_schema=FieldWorkLog.model_json_schema(),
                few_shot_examples=auto_few_shot_examples_str,
                message=message_text,
                schema_hints=auto_schema_hints,
            )
            
            logger.info(f"🔍 Генерация промпта завершена. Длина: {len(system_prompt)} символов")
            
            # Выполняем запрос к модели
            logger.info(f"🧠 Отправка запроса к модели {llm_config.get('llm_model_name')}")
            model_start_time = time.time()
            field_work_log = await model.with_structured_output(FieldWorkLog).ainvoke(
                [SystemMessage(content=system_prompt)]
            )
            model_end_time = time.time()
            logger.info(f"✅ Ответ от модели получен. Время выполнения: {model_end_time - model_start_time:.2f} сек.")
            logger.info(f"📝 Выделено записей: {len(field_work_log.entries)}")
            
            # Добавляем детальное логирование выделенных записей
            for i, entry in enumerate(field_work_log.entries):
                logger.info(f"  📄 Запись #{i+1}:")
                logger.info(f"    🏢 Подразделение: {entry.department_name}")
                logger.info(f"    🔨 Операция: {entry.operation}")
                logger.info(f"    🌱 Культура: {entry.crop}")
                logger.info(f"    📊 Площадь день/всего: {entry.processed_area_day}/{entry.processed_area_total} га")
                if entry.yield_kg_day or entry.yield_kg_total:
                    logger.info(f"    📈 Урожай день/всего: {entry.yield_kg_day or 'Нет'}/{entry.yield_kg_total or 'Нет'} кг")
            
            # Обрабатываем результат
            reports = []
            for entry in field_work_log.entries:
                # Собираем все объяснения для поля note
                explanations = []
                
                try:
                    department_id = _match_department_id(entry.department_name, departments)
                    logger.info(f"   🔍 Сопоставление: {entry.department_name} -> ID: {department_id}")
                    department_raw = None
                    department_predicted = None
                except ValueError as e:
                    department_id = None
                    department_raw = entry.department_name
                    department_predicted = entry.department_name
                    explanations.append(f"Подразделение: {str(e)}")
                    logger.warning(f"   ⚠️ Ошибка сопоставления подразделения: {e}")
                
                try:
                    operation_id = _match_operation_id(entry.operation, operations)
                    logger.info(f"   🔍 Сопоставление: {entry.operation} -> ID: {operation_id}")
                    operation_raw = None
                    operation_predicted = None
                except ValueError as e:
                    operation_id = None
                    operation_raw = entry.operation
                    operation_predicted = entry.operation
                    explanations.append(f"Операция: {str(e)}")
                    logger.warning(f"   ⚠️ Ошибка сопоставления операции: {e}")
                
                try:
                    crop_id = _match_crop_id(entry.crop, crops)
                    logger.info(f"   🔍 Сопоставление: {entry.crop} -> ID: {crop_id}")
                    crop_raw = None
                    crop_predicted = None
                except ValueError as e:
                    crop_id = None
                    crop_raw = entry.crop
                    crop_predicted = entry.crop
                    explanations.append(f"Культура: {str(e)}")
                    logger.warning(f"   ⚠️ Ошибка сопоставления культуры: {e}")
                
                # Создаем note объединением всех объяснений
                note = None
                if explanations:
                    note = "; ".join(explanations)
                    logger.info(f"   📝 Создана заметка: {note}")
                
                # Проверяем, что хотя бы один из ID не None
                if department_id is None and operation_id is None and crop_id is None:
                    logger.warning(f"   ⚠️ Ни одно поле не имеет валидного ID, используем заглушки из первых записей")
                    # Используем первые записи в качестве заглушек, если ни один ID не найден
                    if not department_id and departments:
                        department_id = departments[0].id
                        logger.info(f"   🔧 Установлена заглушка для department_id: {department_id}")
                    if not operation_id and operations:
                        operation_id = operations[0].id
                        logger.info(f"   🔧 Установлена заглушка для operation_id: {operation_id}")
                    if not crop_id and crops:
                        crop_id = crops[0].id
                        logger.info(f"   🔧 Установлена заглушка для crop_id: {crop_id}")
                
                # Преобразование килограммов в центнеры (делим на 100)
                day_yield = None
                cumulative_yield = None
                
                if entry.yield_kg_day is not None:
                    day_yield = entry.yield_kg_day / 100
                    logger.info(f"   📊 Конвертация день, кг -> цн: {entry.yield_kg_day} -> {day_yield}")
                    
                if entry.yield_kg_total is not None:
                    cumulative_yield = entry.yield_kg_total / 100
                    logger.info(f"   📊 Конвертация всего, кг -> цн: {entry.yield_kg_total} -> {cumulative_yield}")
                
                # Проверяем только day_area, так как это обязательное поле
                day_area = entry.processed_area_day
                if day_area is None or day_area <= 0:
                    day_area = 1
                    logger.warning(f"   ⚠️ Некорректное значение day_area: {entry.processed_area_day}, устанавливаем значение 1")
                
                # Сохраняем cumulative_area как None, если модель вернула processed_area_total = None
                cumulative_area = entry.processed_area_total
                
                report = Report(
                    worked_on=message_created_at.date(),
                    chat_message_id=message_id,
                    department_id=department_id,
                    operation_id=operation_id,
                    crop_id=crop_id,
                    department_raw=department_raw,
                    operation_raw=operation_raw,
                    crop_raw=crop_raw,
                    department_predicted=department_predicted,
                    operation_predicted=operation_predicted,
                    crop_predicted=crop_predicted,
                    note=note,
                    day_area=day_area,
                    cumulative_area=cumulative_area,
                    day_yield=day_yield,
                    cumulative_yield=cumulative_yield,
                )
                logger.info(f"   ✅ Объект Report создан с ID: {report.id}")
                reports.append(report)
                
            logger.info(f"   ✅ Создано записей Report: {len(reports)}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в режиме AUTO: {e}", exc_info=True)
            raise

    end_time = time.time()
    logger.info(f"⏱️ Общее время обработки: {end_time - start_time:.2f} сек.")
    return reports
