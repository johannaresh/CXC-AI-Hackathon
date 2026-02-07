from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.audit import router as audit_router
from .api.strategies import router as strategies_router
from .core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("EdgeAudit backend starting up")
    yield
    logger.info("EdgeAudit backend shutting down")


app = FastAPI(
    title="EdgeAudit",
    description="AI-powered quantitative strategy auditing platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(audit_router)
app.include_router(strategies_router)
