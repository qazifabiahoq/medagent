from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from graph.builder import get_checkpointer
from api.routes import cases, stream, approve, history

checkpointer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global checkpointer
    checkpointer = await get_checkpointer(os.getenv("POSTGRES_URL"))
    app.state.checkpointer = checkpointer
    yield
    await checkpointer.conn.close()


app = FastAPI(title="MedAgent API", version="0.1.0", lifespan=lifespan)

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


@app.get("/health")
async def health():
    return {"status": "ok"}
