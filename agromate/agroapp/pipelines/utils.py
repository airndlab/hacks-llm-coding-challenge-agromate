import math

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Dict, Any, List, Tuple

from entities import Department, Operation, Crop


def _match_department_id(name: str, departments: list[Department]) -> int:
    for d in departments:
        if d.department_number == name or d.subdivision == name or (d.aliases and name in d.aliases.split(",")):
            return d.id
    raise ValueError(f"Не найдено подразделение: {name}")

def _match_operation_id(name: str, operations: list[Operation]) -> int:
    for o in operations:
        if o.operation_name == name:
            return o.id
    raise ValueError(f"Не найдена операция: {name}")

def _match_crop_id(name: str, crops: list[Crop]) -> int:
    for c in crops:
        if c.crop_name == name:
            return c.id
    raise ValueError(f"Не найдена культура: {name}")

def extract_department_names(departments: List[Department]) -> Tuple[str, ...]:
    names = set()

    for dept in departments:
        # Добавляем номер отделения (если не "Нет отделения")
        if dept.department_number and dept.department_number != "Нет отделения":
            names.add(dept.department_number.strip())

        # Добавляем подразделение (например, "АОР", "ТСК")
        if dept.subdivision and dept.subdivision != "Нет ПУ":
            names.add(dept.subdivision.strip())

        # Добавляем производственное подразделение (например, "Север", "Центр", ...)
        if dept.production_unit and dept.production_unit != "Нет ПУ":
            names.add(dept.production_unit.strip())

        # Добавляем алиасы, если есть
        if dept.aliases:
            for alias in dept.aliases.split(","):
                alias = alias.strip()
                if alias:
                    names.add(alias)

    return tuple(sorted(names))


def is_empty(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


def generate_field_work_log_schema(
    department_names: Tuple[str],
    operations: Tuple[str],
    crops: Tuple[str],
):
    # Внутренний класс Entry с подстановкой литералов
    class FieldWorkEntry(BaseModel):
        date: Optional[str] = Field(
            None, description="Дата проведения операции (формат: 'мм-дд')"
        )
        department_name: Literal[department_names] = Field(
            ..., description="Название подразделения, в котором проводилась операция"
        )
        operation: Literal[operations] = Field(
            ..., description="Название выполненной операции"
        )
        crop: Literal[crops] = Field(
            ..., description="Культура, к которой относится операция"
        )
        processed_area_day: int = Field(
            ..., description="Обработанная площадь за день, в гектарах"
        )
        processed_area_total: int = Field(
            ..., description="Общая обработанная площадь с начала операции, в гектарах"
        )
        yield_kg_day: Optional[int] = Field(
            None, description="Валовая продукция за день, в килограммах"
        )
        yield_kg_total: Optional[int] = Field(
            None, description="Суммарная валовая продукция с начала операции, в килограммах"
        )

        @field_validator('crop', mode='before')
        @classmethod
        def normalize_crop(cls, value):
            if isinstance(value, str):
                return value.replace('\xa0', ' ').strip()
            return value

        def model_dump_comparable(self) -> Dict[str, Any]:
            dumped = self.model_dump()
            for key, value in dumped.items():
                if is_empty(value):
                    dumped[key] = None
            return dumped

    # Оборачивающий класс
    class FieldWorkLog(BaseModel):
        entries: List[FieldWorkEntry] = Field(
            ..., description="Список записей о полевых операциях"
        )

    return FieldWorkLog