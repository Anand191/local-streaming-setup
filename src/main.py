from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.endpoints import router
from core.logging import logger
from services.kafka_client import kafka_client


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manages startup and shutdown events for the FastAPI app."""
    # Startup
    logger.info("Application startup...")
    await kafka_client.start()
    yield
    # Shutdown
    logger.info("Application shutdown...")
    await kafka_client.stop()


app = FastAPI(lifespan=lifespan)

app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    """Simple root endpoint with welcome msg."""
    return {"message": "Welcome to the Async/Stream Processing POC"}
