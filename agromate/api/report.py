import logging
import os
import tempfile
from datetime import datetime, date

from openpyxl import Workbook

from agroapp.entities import Report

logger = logging.getLogger(__name__)


def create_excel_report(reports: list["Report"], report_on: date) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = f"Полевые работы"

    headers = [
        "Дата",
        "Подразделение",
        "Операция",
        "Культура",
        "За день, га",
        "С начала операции, га",
        "Вал за день, ц",
        "Вал с начала, ц"
    ]
    ws.append(headers)

    for report in reports:
        date_str = report.worked_on.strftime("%Y-%m-%d") if isinstance(report.worked_on, datetime) else str(
            report.worked_on)

        department_subdivision = report.department.subdivision if report.department else ""
        operation_name = report.operation.operation_name if report.operation else ""
        crop_name = report.crop.crop_name if report.crop else ""

        row = [
            date_str,  # Дата
            department_subdivision,  # Подразделение
            operation_name,  # Операция
            crop_name,  # Культура
            report.day_area,  # За день, га
            report.cumulative_area,  # С начала операции, га
            report.day_yield if report.day_yield is not None else "",  # Вал за день, ц
            report.cumulative_yield if report.cumulative_yield is not None else ""  # Вал с начала, ц
        ]
        ws.append(row)

    filename = f"{report_on.strftime('%d%m%Y')}.xlsx"
    file_path = os.path.join(tempfile.gettempdir(), filename)

    with open(file_path, "w+t"):
        wb.save(file_path)
        logger.info(f"Created report on '{report_on}': {file_path}")
        return file_path
