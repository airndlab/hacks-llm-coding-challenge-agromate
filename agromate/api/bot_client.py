import aiohttp

from agroapp.config import settings
from agroapp.models import ChatMessageReactionRequest


async def send_reactions(payload: ChatMessageReactionRequest):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                f'{settings.bot_url}/api/sending/reactions',
                headers={"Content-Type": "application/json"},
                data=payload.model_dump_json(),
        ) as response:
            if response.status != 200:
                raise Exception(f"Error: {response.status} {await response.text()}")
