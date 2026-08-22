"""FastAPI app.

Init DB saat startup + pasang seluruh router. Loop penuh M4: node/attempt/probe
(akuisisi) + placement (menemukan lantai) + review (jatuh tempo) + stats (KPI).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGIN
from app.db import init_db
from app.routers import attempts, authoring, nodes, placement, probes, review, stats


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
app.include_router(placement.router)
app.include_router(review.router)
app.include_router(stats.router)
# M5 — integrasi Claude Code. Router ini boleh mati (kill switch) tanpa mengubah
# apa pun di router di atasnya.
app.include_router(authoring.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
