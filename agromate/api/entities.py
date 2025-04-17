from datetime import date, datetime, UTC
from typing import Optional, List

from sqlmodel import Field, SQLModel, Relationship

from agroapp.models import MessageStatus


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    chat_id: str
    message_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    message_text: str
    status: MessageStatus = Field(default=MessageStatus.new)
    status_text: Optional[str] = None

    report: List["Report"] = Relationship(back_populates="chat_message")

class Department(SQLModel, table=True):
    __tablename__ = "department"

    id: Optional[int] = Field(default=None, primary_key=True)
    subdivision: str = Field(index=True)
    production_unit: str
    department_number: str
    aliases: Optional[str] = None

    report: List["Report"] = Relationship(back_populates="department")


class Operation(SQLModel, table=True):
    __tablename__ = "operation"

    id: Optional[int] = Field(default=None, primary_key=True)
    operation_name: str
    note: Optional[str] = None
    aliases: Optional[str] = None

    report: List["Report"] = Relationship(back_populates="operation")


class Crop(SQLModel, table=True):
    __tablename__ = "crop"

    id: Optional[int] = Field(default=None, primary_key=True)
    crop_name: str
    aliases: Optional[str] = None

    report: List["Report"] = Relationship(back_populates="crop")


class Report(SQLModel, table=True):
    __tablename__ = "report"

    id: Optional[int] = Field(default=None, primary_key=True)
    worked_on: date

    chat_message_id: int = Field(foreign_key="chat_message.id")
    department_id: int = Field(foreign_key="department.id")
    operation_id: int = Field(foreign_key="operation.id")
    crop_id: int = Field(foreign_key="crop.id")

    day_area: float
    cumulative_area: float
    day_yield: float
    cumulative_yield: float

    chat_message: Optional[ChatMessage] = Relationship(back_populates="report")
    department: Optional[Department] = Relationship(back_populates="report")
    operation: Optional[Operation] = Relationship(back_populates="report")
    crop: Optional[Crop] = Relationship(back_populates="report")


