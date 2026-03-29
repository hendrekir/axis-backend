import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import engine, Base, async_session
from routes.auth import get_current_user
from routes.thread import router as thread_router
from routes.signals import router as signals_router
from routes.brain_dump import router as brain_dump_router
from routes.brief import router as brief_router
from routes.skills import router as skills_router
from routes.payments import router as payments_router
from routes.push import router as push_router
from routes.gmail import router as gmail_router
from routes.cron import router as cron_router
from routes.me import router as me_router
from routes.billing import router as billing_router
from services.dispatch import run_dispatch
from services.morning_digest import run_morning_digest

load_dotenv()

logger = logging.getLogger("axis.scheduler")

# Public routes that skip auth
PUBLIC_PATHS = {"/", "/health", "/webhooks/revenuecat", "/webhooks/stripe", "/auth/gmail", "/auth/gmail/callback", "/cron/dispatch", "/cron/digest"}


async def _scheduled_dispatch():
    """Wrapper to run dispatch inside its own DB session."""
    async with async_session() as db:
        try:
            stats = await run_dispatch(db)
            logger.info("Dispatch complete: %d users processed", len(stats))
        except Exception as e:
            logger.error("Dispatch job failed: %s", e)


async def _scheduled_digest():
    """Wrapper to run morning digest inside its own DB session."""
    async with async_session() as db:
        try:
            results = await run_morning_digest(db)
            logger.info("Digest complete: %d digests sent", len(results))
        except Exception as e:
            logger.error("Digest job failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_scheduled_dispatch, "interval", minutes=15, id="dispatch")
    scheduler.add_job(_scheduled_digest, "interval", minutes=15, id="digest")
    scheduler.start()
    logger.info("Scheduler started — dispatch and digest every 15 minutes")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(title="Axis Backend", version="1.0.0", lifespan=lifespan)

# CORS — allow iOS app and web origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    # Verify auth token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing or invalid authorization header"},
        )

    token = auth_header.split(" ", 1)[1]
    user = await get_current_user(token)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token"},
        )

    # Attach user to request state for downstream routes
    request.state.user = user
    return await call_next(request)


# Routes
app.include_router(thread_router, prefix="/thread", tags=["Thread"])
app.include_router(signals_router, tags=["Signals"])
app.include_router(brain_dump_router, tags=["Brain Dump"])
app.include_router(brief_router, tags=["Brief"])
app.include_router(skills_router, tags=["Skills"])
app.include_router(payments_router, prefix="/webhooks", tags=["Payments"])
app.include_router(push_router, tags=["Push"])
app.include_router(gmail_router, tags=["Gmail"])
app.include_router(cron_router, tags=["Cron"])
app.include_router(me_router, tags=["User"])
app.include_router(billing_router, tags=["Billing"])


@app.get("/")
async def root():
    return {"service": "Axis Backend", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


