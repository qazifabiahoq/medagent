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
    # Pre-load embedding model so the first request doesn't pay the cold-start cost
    try:
        import asyncio
        from memory.embedder import get_embedder
        await asyncio.get_event_loop().run_in_executor(None, get_embedder)
        logger.info("Embedding model pre-loaded")
    except Exception as e:
        logger.warning("Embedding pre-load skipped: %s", e)

    postgres_url = os.getenv("POSTGRES_URL", "")
    app.state.checkpointer = None

    if postgres_url:
        try:
            from graph.checkpointer import get_checkpointer_context
            ctx = get_checkpointer_context(postgres_url)
            async with ctx as checkpointer:
                await checkpointer.setup()
                app.state.checkpointer = checkpointer
                logger.info("Checkpointer connected")
                yield
                return
        except Exception as e:
            logger.error("Checkpointer failed: %s", e)

    # Fallback: run without checkpointer
    yield


app = FastAPI(
    title="MedAgent API",
    version="1.0.0",
    description="Clinical Intelligence Platform",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
        "checkpointer": app.state.checkpointer is not None,
    }
