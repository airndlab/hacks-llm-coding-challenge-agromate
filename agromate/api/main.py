import logging

import uvicorn
from fastapi import FastAPI

from agroapp.api import router
from agroapp.config import settings
from agroapp.hooks import life_hook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgroMate App API",
    description="""
    AgroMate App
    """,
    version="0.1.0",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 3,
        "deepLinking": True
    },
    lifespan=life_hook,
    debug=settings.debug,
)

app.include_router(router)


@app.get("/")
async def status():
    return {"status": "UP"}


if __name__ == "__main__":
    uvicorn.run("agroapp.main:app", host="0.0.0.0", port=8080)
