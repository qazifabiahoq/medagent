from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os

from graph.checkpointer import create_checkpointer
from api.routes import cases, stream, approve, history
from api.middleware import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    postgres_url = os.getenv("POSTGRES_URL", "postgresql://medagent:medagent@postgres:5432/medagent")
    checkpointer = await create_checkpointer(postgres_url)
    app.state.checkpointer = checkpointer
    yield
    try:
        await checkpointer.conn.aclose()
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
    }
