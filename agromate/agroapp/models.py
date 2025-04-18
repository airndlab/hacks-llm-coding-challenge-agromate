from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class MessageType(str, Enum):
    spam = "spam"
    report = "report"


class MessageStatus(str, Enum):
    new = "new"
    spam = "spam"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class ChatMessageCreateRequest(BaseModel):
    username: str
    user_id: str
    chat_id: str
    message_id: str
    message_text: str
    created_at: datetime


class ChatMessageCreateResponse(BaseModel):
    id: int


class ChatMessageReactionRequest(BaseModel):
    chat_id: str
    message_id: str
    status: MessageStatus


class ChatMessageReplyRequest(BaseModel):
    chat_id: str
    message_id: str
    text: str


class ReportResponse(BaseModel):
    created_at: datetime
    url: str
    summary: str
