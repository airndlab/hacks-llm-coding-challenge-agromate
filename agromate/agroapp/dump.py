import logging
import os
import tempfile
from datetime import date

from docx import Document
from openpyxl.workbook import Workbook

from config import settings
from entities import ChatMessage, Department, Operation, Crop
from entities import Report
from google_drive import upload_word_file_to_folder, upload_excel_file_to_folder, overwrite_excel_file_by_id
from report import append_reports_to_excel, create_excel_report, save_excel

logger = logging.getLogger(__name__)

_current_report_on: date | None = None
_current_wb: Workbook | None = None
_current_next_row: int | None = None
_current_file_id: str | None = None


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

        with open(file_path, "w+t"):
            doc.save(file_path)

        upload_word_file_to_folder(file_path)
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


import datetime
from models import MessageStatus

cm = ChatMessage(
    id=1,
    serial_num=300,
    username='FooBar',
    user_id='',
    chat_id='',
    message_id='',
    created_at=datetime.datetime.utcnow(),
    message_text='Hello\nAll',
    status=MessageStatus.new,
    status_text='',
)
# dump_message_silently(cm)
dump_report_silently(cm, [
    Report(
        id=1,
        worked_on=datetime.datetime.utcnow().date(),
        chat_message_id='',
        department_id='',
        operation_id='',
        crop_id='',
        department_raw='',
        operation_raw='',
        crop_raw='',
        department_predicted='',
        operation_predicted='',
        crop_predicted='',
        note='',
        day_area=100.11,
        cumulative_area=123.24,
        day_yield=24.3,
        cumulative_yield=123456.78,
        chat_message=cm,
        department=Department(
            subdivision='Отдел из справочника'
        ),
        operation=Operation(
            operation_name='Операция из справочника'
        ),
        crop=Crop(
            crop_name='Культура из справочника'
        ),
    ),
    Report(
        id=1,
        worked_on=datetime.datetime.utcnow().date(),
        chat_message_id='',
        department_id='',
        operation_id='',
        crop_id='',
        department_raw='Отдел сырое',
        operation_raw='Операция сырое',
        crop_raw='Культура сырое',
        department_predicted='',
        operation_predicted='',
        crop_predicted='',
        note='',
        day_area=100.11,
        cumulative_area=123.24,
        day_yield=24.3,
        cumulative_yield=123456.78,
        chat_message=cm,
        department=None,
        operation=None,
        crop=None,
    ),
    Report(
        id=1,
        worked_on=datetime.datetime.utcnow().date(),
        chat_message_id='',
        department_id='',
        operation_id='',
        crop_id='',
        department_raw=None,
        operation_raw=None,
        crop_raw=None,
        department_predicted='Отдел предсказанные',
        operation_predicted='Операция предсказанные',
        crop_predicted='Культура предсказанные',
        note='',
        day_area=100.11,
        cumulative_area=123.24,
        day_yield=24.3,
        cumulative_yield=123456.78,
        chat_message=cm,
        department=None,
        operation=None,
        crop=None,
    )

])

# dump_report_silently(cm, [
#     Report(
#         id=2,
#         worked_on=datetime.datetime.utcnow().date(),
#         chat_message_id='',
#         department_id='',
#         operation_id='',
#         crop_id='',
#         department_raw='',
#         operation_raw='',
#         crop_raw='',
#         department_predicted='',
#         operation_predicted='',
#         crop_predicted='',
#         note='',
#         day_area=62.24,
#         cumulative_area=2457752.55,
#         day_yield=2457.57,
#         cumulative_yield=57.78,
#         chat_message=cm,
#         department=Department(
#             subdivision='Отдел 2'
#         ),
#         operation=Operation(
#             operation_name='Операция 2'
#         ),
#         crop=Crop(
#             crop_name='Культура 2'
#         ),
#     ),
# ])
