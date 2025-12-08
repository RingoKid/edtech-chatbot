import os
from fastapi import FastAPI, HTTPException, APIRouter, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.routers import health, chat, auth, users
from app.config import settings
from app.dependencies.auth import get_current_user

# Configuration
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

# Initialize LangSmith tracing
settings.initialize_langsmith()

# Initialize the FastAPI application
app = FastAPI(
    title="EdTech Chatbot API",
    description="AI-powered chatbot for early childhood education",
    version="1.0.0"
)

# Add CORS middleware (for httpOnly cookies and credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],  # Frontend URL from config
    allow_credentials=True,  # REQUIRED for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Public Routes (no authentication required) ---
public_router = APIRouter(prefix=API_PREFIX)
public_router.include_router(auth.router)  # /api/v1/auth/*
public_router.include_router(health.router)  # /api/v1/health (public for health checks)

# --- Protected Routes (require authentication globally) ---
protected_router = APIRouter(
    prefix=API_PREFIX,
    dependencies=[Depends(get_current_user)]  # Applied to ALL routes in this router
)

# Include protected routers
protected_router.include_router(chat.router)
protected_router.include_router(users.router)

# Mount routers to app
app.include_router(public_router)
app.include_router(protected_router)

# Root health check endpoint (public, no prefix)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "edtech-chatbot-api"}
