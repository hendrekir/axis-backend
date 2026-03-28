import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import engine, Base
from routes.auth import get_current_user
from routes.thread import router as thread_router
from routes.signals import router as signals_router
from routes.brain_dump import router as brain_dump_router
from routes.brief import router as brief_router
from routes.skills import router as skills_router
from routes.payments import router as payments_router
from routes.push import router as push_router

load_dotenv()

# Public routes that skip auth
PUBLIC_PATHS = {"/", "/health", "/webhooks/revenuecat", "/brain-dump"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Dispose connection pool on shutdown
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


@app.get("/")
async def root():
    return {"service": "Axis Backend", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
