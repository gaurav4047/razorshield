import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import audit, batch, cases, webhooks
from app.scheduler.jobs import start_scheduler, stop_scheduler

AUDIO_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "audio")
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background scheduler loop per 01_architecture.md §4
    start_scheduler(interval_seconds=15)
    yield
    # Shutdown: Cleanly stop background tasks
    stop_scheduler()


app = FastAPI(
    title="Razorpay AI Revenue Recovery",
    description="Multi-class revenue recovery intelligence platform",
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

# API Routers per 07_frontend_dashboard.md §1
app.include_router(cases.router, prefix="/api/cases", tags=["cases"])
app.include_router(batch.router, prefix="/api/batches", tags=["batches"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(audit.router, prefix="/ws/audit", tags=["ws-audit"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Mount static audio files storage
app.mount("/audio", StaticFiles(directory=AUDIO_STORAGE_DIR), name="audio")


@app.get("/health")
async def health_check():
    return {"status": "ok"}

