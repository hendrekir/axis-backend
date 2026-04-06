import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from sqlalchemy import text
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
from routes.calendar import router as calendar_router
from routes.spotify import router as spotify_router
from routes.apprentice import router as apprentice_router
from routes.notes import router as notes_router
from routes.tts import router as tts_router
from routes.cron import router as cron_router
from routes.me import router as me_router
from routes.billing import router as billing_router
from routes.schedule import router as schedule_router
from routes.quick_capture import router as quick_capture_router
from routes.insights import router as insights_router
from routes.journal import router as journal_router
from routes.capture import router as capture_router
from services.dispatch import run_dispatch
from services.morning_digest import run_morning_digest
from services.apprentice import run_all_improvement, run_all_voice_rebuild
from services.watch_service import run_all_watches
from services.retrospective_service import run_all_retrospectives
from services.meeting_prep import run_meeting_prep

load_dotenv()

logger = logging.getLogger("axis.scheduler")

# Public routes that skip auth
PUBLIC_PATHS = {"/", "/health", "/capture/test", "/webhooks/revenuecat", "/webhooks/stripe", "/auth/gmail", "/auth/gmail/callback", "/auth/calendar", "/auth/calendar/callback", "/auth/spotify", "/auth/spotify/callback", "/cron/dispatch", "/cron/digest", "/cron/streak-reminder", "/cron/journal-prompt"}


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


async def _scheduled_improvement():
    """Sunday 3AM UTC: run improvement cycle for all Pro users."""
    async with async_session() as db:
        try:
            results = await run_all_improvement(db)
            logger.info("Improvement cycle complete: %d users processed", len(results))
        except Exception as e:
            logger.error("Improvement cycle failed: %s", e)


async def _scheduled_voice_rebuild():
    """Sunday 4AM UTC: rebuild voice models for all Pro+Gmail users."""
    async with async_session() as db:
        try:
            results = await run_all_voice_rebuild(db)
            logger.info("Voice rebuild complete: %d users processed", len(results))
        except Exception as e:
            logger.error("Voice rebuild failed: %s", e)


async def _scheduled_retrospective():
    """Sunday 6PM UTC: generate and send weekly retrospectives for Pro users."""
    async with async_session() as db:
        try:
            results = await run_all_retrospectives(db)
            logger.info("Retrospectives complete: %d users", len(results))
        except Exception as e:
            logger.error("Retrospective job failed: %s", e)


async def _scheduled_watches():
    """Hourly: check all active watches for material changes."""
    async with async_session() as db:
        try:
            alerts = await run_all_watches(db)
            if alerts:
                logger.info("Watch cycle: %d alerts triggered", len(alerts))
        except Exception as e:
            logger.error("Watch cycle failed: %s", e)


async def _scheduled_meeting_prep():
    """Every 5 minutes: check for meetings starting in 25-35 minutes, generate briefs."""
    async with async_session() as db:
        try:
            results = await run_meeting_prep(db)
            if results:
                logger.info("Meeting prep: %d briefs generated", len(results))
        except Exception as e:
            logger.error("Meeting prep job failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Migrate columns added after initial table creation
    async with engine.begin() as conn:
        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS calendar_access_token TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS calendar_refresh_token TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS calendar_token_expiry TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS calendar_connected BOOLEAN DEFAULT FALSE",
            # Streak + context columns (Session 7)
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS context_notes TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS current_streak INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS longest_streak INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active_date DATE",
            # Notes table + GIN full-text index (Session 7)
            """CREATE TABLE IF NOT EXISTS notes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                content TEXT NOT NULL,
                tags TEXT[] DEFAULT '{}',
                source TEXT DEFAULT 'thread',
                context_snapshot JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW()
            )""",
            "CREATE INDEX IF NOT EXISTS ix_notes_content_fts ON notes USING gin(to_tsvector('english', content))",
            # Watches table (Session 7)
            """CREATE TABLE IF NOT EXISTS watches (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                topic TEXT NOT NULL,
                watch_type TEXT DEFAULT 'general',
                last_checked_at TIMESTAMP,
                last_result TEXT,
                threshold TEXT DEFAULT 'material_change',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            )""",
            # Follow-ups table (Session 7)
            """CREATE TABLE IF NOT EXISTS follow_ups (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                email_id TEXT,
                to_email TEXT,
                subject TEXT,
                sent_at TIMESTAMP,
                follow_up_due TIMESTAMP,
                followed_up_at TIMESTAMP,
                is_done BOOLEAN DEFAULT FALSE
            )""",
            # Weekly retrospectives table (Session 7)
            """CREATE TABLE IF NOT EXISTS weekly_retrospectives (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                week_start DATE,
                content TEXT,
                sent_at TIMESTAMP
            )""",
            # Skill suggestions table (Session 7)
            """CREATE TABLE IF NOT EXISTS skill_suggestions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                pattern_detected TEXT NOT NULL,
                suggested_name TEXT NOT NULL,
                suggested_config JSONB DEFAULT '{}',
                suggested_at TIMESTAMP DEFAULT NOW(),
                accepted BOOLEAN DEFAULT FALSE,
                dismissed BOOLEAN DEFAULT FALSE
            )""",
            # Journal entries table (Session 11)
            # Thread message archival for Dream feature (Session 12)
            "ALTER TABLE thread_messages ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE",
            # Signal deduplication table (Session 14)
            """CREATE TABLE IF NOT EXISTS dispatched_signals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                signal_key TEXT NOT NULL,
                surface TEXT NOT NULL,
                urgency INTEGER DEFAULT 5,
                dispatched_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, signal_key)
            )""",
            "CREATE INDEX IF NOT EXISTS ix_dispatched_signals_user_at ON dispatched_signals(user_id, dispatched_at)",
            """CREATE TABLE IF NOT EXISTS journal_entries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                date DATE NOT NULL,
                extracted_people JSONB,
                extracted_projects JSONB,
                extracted_emotions JSONB,
                extracted_context TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )""",
        ]
        for sql in migrations:
            await conn.execute(text(sql))
        logger.info("Startup migrations applied (%d statements)", len(migrations))

    # Start scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_scheduled_dispatch, "interval", minutes=15, id="dispatch")
    scheduler.add_job(_scheduled_digest, "interval", minutes=15, id="digest")
    scheduler.add_job(_scheduled_watches, "interval", hours=1, id="watches")
    scheduler.add_job(_scheduled_meeting_prep, "interval", minutes=5, id="meeting_prep")
    scheduler.add_job(_scheduled_improvement, "cron", day_of_week="sun", hour=3, minute=0, id="improvement")
    scheduler.add_job(_scheduled_voice_rebuild, "cron", day_of_week="sun", hour=4, minute=0, id="voice_rebuild")
    scheduler.add_job(_scheduled_retrospective, "cron", day_of_week="sun", hour=18, minute=0, id="retrospective")
    scheduler.start()
    logger.info("Scheduler started — dispatch/digest 15min, watches hourly, meeting prep 5min, improvement Sun 3AM, voice Sun 4AM, retro Sun 6PM")

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

    # Simulator dev bypass — skip JWT, use hardcoded test user
    if request.headers.get("X-Dev-Simulator") == "true":
        class SimulatorUser:
            def __init__(self):
                self.clerk_id = "simulator_test_user"
                self.claims = {"sub": "simulator_test_user", "name": "Test User"}
        request.state.user = SimulatorUser()
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
app.include_router(calendar_router, tags=["Calendar"])
app.include_router(spotify_router, tags=["Spotify"])
app.include_router(apprentice_router, tags=["Apprentice"])
app.include_router(notes_router, tags=["Notes"])
app.include_router(tts_router, tags=["TTS"])
app.include_router(cron_router, tags=["Cron"])
app.include_router(me_router, tags=["User"])
app.include_router(billing_router, tags=["Billing"])
app.include_router(schedule_router, tags=["Schedule"])
app.include_router(quick_capture_router, tags=["Quick Capture"])
app.include_router(insights_router, tags=["Insights"])
app.include_router(journal_router, tags=["Journal"])
app.include_router(capture_router, tags=["Capture"])


@app.get("/")
async def root():
    return {"service": "Axis Backend", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


