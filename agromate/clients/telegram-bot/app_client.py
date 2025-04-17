import aiohttp

from config import settings
from models import ChatMessageCreateRequest, ChatMessageCreateResponse


async def create_message(payload: ChatMessageCreateRequest) -> ChatMessageCreateResponse:
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f'{settings.app_url}/api/messages',
                headers={"Content-Type": "application/json"},
                data=payload.model_dump_json(),
        ) as response:
            if response.status == 200:
                json = await response.json()
                return ChatMessageCreateResponse(**json)
            else:
                raise Exception(f"Error: {response.status} {await response.text()}")
