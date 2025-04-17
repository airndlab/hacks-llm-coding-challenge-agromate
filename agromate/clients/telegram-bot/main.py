import asyncio
import logging
import sys

from bot import bot_client
from api import start_api
from dispatch import start_pooling

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    await asyncio.gather(
        start_pooling(bot_client),
        start_api()
    )

if __name__ == "__main__":
    asyncio.run(main())
