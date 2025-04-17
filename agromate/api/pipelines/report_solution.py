import os

from datetime import datetime

from pathlib import Path
import yaml

from .utils import (
    extract_department_names,
    generate_field_work_log_schema,
    _match_department_id,
    _match_crop_id,
    _match_operation_id,
)

from agroapp.config import settings
from agroapp.entities import Report, Department, Operation, Crop

from jinja2 import Template

from langchain_openai import ChatOpenAI

from langchain_core.messages import SystemMessage

import logging

logger = logging.getLogger(__name__)

llm_config_path = os.path.join(settings.configs_path, "llm.yaml")
prompts_config_path = os.path.join(settings.configs_path, "prompts.yaml")

with open(Path(llm_config_path), mode="r", encoding="utf-8") as f:
    llm_config = yaml.safe_load(f)

with open(Path(prompts_config_path), mode="r", encoding="utf-8") as f:
    prompts_config = yaml.safe_load(f)

SYSTEM_PROMPT_TEMPLATE = Template(prompts_config.get("baseline_system_prompt_template"))
schema_hints = prompts_config.get("schema_hints")
few_shot_examples_str = prompts_config.get("few_shot_examples_str")

model = ChatOpenAI(
    model=llm_config.get("model_name"),
    openai_api_key=settings.llm_api_key,
    openai_api_base=settings.llm_api_base_url,
)


async def solve_reports(
        message_id: int,
        message_text: str,
        message_created_at: datetime,
        departments: list[Department],
        crops: list[Crop],
        operations: list[Operation],
) -> list[Report]:

    # Извлекаем имена для Literal-типов
    department_names = extract_department_names(departments)
    crop_names = tuple(crop.crop_name for crop in crops)
    operation_names = tuple(op.operation_name for op in operations)

    # Генерируем Pydantic-схему
    FieldWorkLog = generate_field_work_log_schema(
        department_names=department_names,
        operations=operation_names,
        crops=crop_names,
    )

    logger.info(f"Текущая схема для Structured Output : {FieldWorkLog.model_json_schema()}")

    system_prompt = SYSTEM_PROMPT_TEMPLATE.render(
        json_schema=FieldWorkLog.model_json_schema(),
        few_shot_examples=few_shot_examples_str,
        message=message_text,
        schema_hints=schema_hints,
    )

    field_work_log: FieldWorkLog = await model.with_structured_output(FieldWorkLog).ainvoke(
        [SystemMessage(content=system_prompt)]
    )

    reports: list[Report] = []

    for entry in field_work_log.entries:
        department_id = _match_department_id(entry.department_name, departments)
        operation_id = _match_operation_id(entry.operation, operations)
        crop_id = _match_crop_id(entry.crop, crops)

        report = Report(
            worked_on=message_created_at.date(),
            chat_message_id=message_id,
            department_id=department_id,
            operation_id=operation_id,
            crop_id=crop_id,
            day_area=entry.processed_area_day,
            cumulative_area=entry.processed_area_total,
            day_yield=entry.yield_kg_day,
            cumulative_yield=entry.yield_kg_total,
        )
        reports.append(report)

    return reports
