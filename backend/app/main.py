"""FastAPI app — M0 scaffolding.

Belum ada fitur; hanya rangka hidup: init DB saat startup + route /health.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGIN
from app.db import init_db
from app.routers import attempts, nodes, probes


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Reproduction Learning Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(nodes.router)
app.include_router(attempts.router)
app.include_router(probes.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
