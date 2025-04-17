import random
from datetime import datetime

from agroapp.entities import Report, Department, Operation, Crop


async def solve_reports(
        message_id: int,
        message_text: str,
        message_created_at: datetime,
        departments: list[Department],
        crops: list[Crop],
        operations: list[Operation],
) -> list[Report]:
    # TODO: Add pipeline
    if message_text.lower().startswith("report-failed"):
        raise Exception("Что-то пошло не так в ходе разбора сообщения отчета...")
    return [Report(
        worked_on=message_created_at.date(),
        chat_message_id=message_id,
        department_id=random.choice(departments).id,
        operation_id=random.choice(operations).id,
        crop_id=random.choice(crops).id,
        day_area=.1,
        cumulative_area=.2,
        day_yield=.3,
        cumulative_yield=.4,
    )]
