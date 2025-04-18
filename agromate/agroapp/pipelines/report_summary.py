import logging
from collections import Counter
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from jinja2 import Template

from config import settings
from entities import Report

import yaml
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Загружаем конфигурацию
llm_config_path = os.path.join(settings.configs_path, "models.yaml")
prompts_config_path = os.path.join(settings.configs_path, "prompts.yaml")

with open(Path(llm_config_path), mode="r", encoding="utf-8") as f:
    llm_config = yaml.safe_load(f)

with open(Path(prompts_config_path), mode="r", encoding="utf-8") as f:
    prompts_config = yaml.safe_load(f)

# Инициализируем модель
model = ChatOpenAI(
    model=llm_config.get("llm_model_name"),
    openai_api_key=settings.llm_api_key,
    openai_api_base=settings.llm_api_base_url,
    max_retries=30,
    timeout=90,
)

# Загружаем шаблон для системного промпта из конфигурации
SYSTEM_PROMPT_TEMPLATE = Template(prompts_config.get("prompt_report_summary"))

async def summarize_reports(reports: list[Report]) -> str:
    """
    Анализирует отчеты, фильтрует записи с непустыми заметками (errors),
    собирает статистику по отделам и создает сводку с помощью LLM.
    
    Args:
        reports: Список объектов Report для анализа
        
    Returns:
        Строка с анализом проблемных отчетов
    """
    logger.info(f"Начинаем анализ {len(reports)} отчетов")
    
    # Фильтруем только отчеты с непустыми note
    problematic_reports = [report for report in reports if report.note]
    
    if not problematic_reports:
        return "Отчеты не содержат записей с проблемами."
    
    logger.info(f"Найдено {len(problematic_reports)} проблемных отчетов")
    
    # Подсчитываем статистику по отделам
    department_counter = Counter()
    for report in reports:
        dept_name = report.department.subdivision if report.department else "Неизвестный отдел"
        department_counter[dept_name] += 1
    
    # Подсчитываем статистику по отделам с проблемами
    problem_dept_counter = Counter()
    for report in problematic_reports:
        dept_name = report.department.subdivision if report.department else "Неизвестный отдел"
        problem_dept_counter[dept_name] += 1
    
    # Формируем текст статистики по отделам
    department_stats = "\n".join([
        f"- {dept}: всего записей {count}, проблемных: {problem_dept_counter.get(dept, 0)}" 
        for dept, count in department_counter.items()
    ])
    
    # Подготавливаем данные проблемных отчетов для LLM
    problem_reports_text = ""
    for i, report in enumerate(problematic_reports, 1):
        dept = report.department.subdivision if report.department else "Неизвестный отдел"
        operation = report.operation.operation_name if report.operation else "Неизвестная операция"
        crop = report.crop.crop_name if report.crop else "Неизвестная культура"
        
        problem_reports_text += f"{i}. Отдел: {dept}\n"
        problem_reports_text += f"   Операция: {operation}\n"
        problem_reports_text += f"   Культура: {crop}\n"
        problem_reports_text += f"   Площадь за день: {report.day_area} га\n"
        if report.cumulative_area:
            problem_reports_text += f"   Общая площадь: {report.cumulative_area} га\n"
        if report.day_yield:
            problem_reports_text += f"   Урожай за день: {report.day_yield} кг\n"
        if report.cumulative_yield:
            problem_reports_text += f"   Общий урожай: {report.cumulative_yield} кг\n"
        problem_reports_text += f"   Проблема: {report.note}\n\n"
    
    # Формируем системный промпт с использованием шаблона из конфигурации
    system_prompt = SYSTEM_PROMPT_TEMPLATE.render(
        department_stats=department_stats,
        problematic_reports=problem_reports_text
    )
    
    # Отправляем запрос к модели
    logger.info(f"Отправка запроса к LLM модели {llm_config.get('llm_model_name')}")
    try:
        response = await model.ainvoke(
            [SystemMessage(content=system_prompt)]
        )
        
        # Добавляем статистику в начало ответа
        summary = f"Всего отчетов: {len(reports)}, из них проблемных: {len(problematic_reports)}\n\n"
        summary += response.content

        return summary
    except Exception as e:
        logger.error(f"Ошибка при вызове LLM: {str(e)}", exc_info=True)
        return f"Ошибка при анализе отчетов: {str(e)}"
