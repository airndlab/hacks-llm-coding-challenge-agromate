import logging
import os
import tempfile
from datetime import date
from typing import Optional

from docx import Document
from openpyxl.workbook import Workbook

from config import settings
from entities import ChatMessage
from entities import Report
from google_drive import upload_word_file_to_folder, upload_excel_file_to_folder, overwrite_excel_file_by_id
from report import append_reports_to_excel, create_excel_report, save_excel

logger = logging.getLogger(__name__)

_current_report_on: Optional[date] = None
_current_wb: Optional[Workbook] = None
_current_next_row: Optional[int] = None
_current_file_id: Optional[str] = None


def dump_message_silently(chat_message: ChatMessage):
    try:
        doc = Document()
        for line in chat_message.message_text.splitlines() or [""]:
            doc.add_paragraph(line)

        ts = chat_message.created_at.strftime("%M%H%d%m%Y")
        safe_username = chat_message.username.replace(" ", "_")
        # ИмяОтправителя_Номер-сообщения_МинутаЧасДеньМесяцГод
        filename = f"{safe_username}_{chat_message.serial_num}_{ts}.docx"
        file_path = os.path.join(tempfile.gettempdir(), filename)
        # ДеньМесяцГод
        subfolder_name = f"Сообщения от {chat_message.created_at.strftime('%d.%m.%Y')}"

        with open(file_path, "w+t"):
            doc.save(file_path)

        upload_word_file_to_folder(file_path, subfolder_name)
        logger.info(f"Created message dump file: {file_path}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


def dump_report_silently(chat_message: ChatMessage, reports: list[Report]):
    global _current_wb, _current_next_row, _current_report_on, _current_file_id
    try:
        report_on = chat_message.created_at.date()
        if _current_wb is None or _current_report_on != report_on:
            _current_wb, _current_next_row = create_excel_report(report_on, reports)
            _current_report_on = report_on
            _current_file_id = None
        else:
            _current_next_row = append_reports_to_excel(_current_wb, _current_next_row, reports)

        ts = chat_message.created_at.strftime("%H%d%m%Y")
        # ЧасДеньМесяцГод_НазваниеКоманды
        filename = f"{ts}_{settings.team_name}.xlsx"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        save_excel(_current_wb, file_path)

        if _current_file_id is None:
            _current_file_id, _ = upload_excel_file_to_folder(file_path)
            logger.info(f"Created report dump file: {file_path}")
        else:
            overwrite_excel_file_by_id(_current_file_id, file_path)
            logger.info(f"Updated report dump file: {file_path}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
