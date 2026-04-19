from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os

from api.routes import cases, stream, approve, history
from api.middleware import RequestLoggingMiddleware

logger = logging.getLogger("medagent.startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Try to connect to Postgres checkpointer — fail gracefully so the
    # server still starts and /health responds even if DB is unreachable.
    try:
        from graph.checkpointer import create_checkpointer
        postgres_url = os.getenv("POSTGRES_URL", "")
        if postgres_url:
            checkpointer = await create_checkpointer(postgres_url)
            app.state.checkpointer = checkpointer
            logger.info("Checkpointer connected successfully")
        else:
            app.state.checkpointer = None
            logger.warning("POSTGRES_URL not set — checkpointer disabled")
    except Exception as e:
        app.state.checkpointer = None
        logger.error("Checkpointer failed to initialise: %s", e)

    yield

    try:
        cp = getattr(app.state, "checkpointer", None)
        if cp:
            await cp.conn.aclose()
    except Exception:
        pass


app = FastAPI(
    title="MedAgent API",
    version="1.0.0",
    description="Clinical Intelligence Platform — multi-agent AI for structured SOAP note generation",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router, prefix="/cases", tags=["cases"])
app.include_router(stream.router, prefix="/stream", tags=["stream"])
app.include_router(approve.router, prefix="/approve", tags=["approve"])
app.include_router(history.router, prefix="/history", tags=["history"])


@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "checkpointer": getattr(app.state, "checkpointer", None) is not None,
    }
