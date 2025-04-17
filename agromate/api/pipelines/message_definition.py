from agroapp.models import MessageType


async def define_message_type(text: str) -> MessageType:
    # TODO: Add pipeline
    if text.lower().startswith("upload"):
        return MessageType.upload
    return MessageType.report
