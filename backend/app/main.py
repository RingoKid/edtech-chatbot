import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.routers import health, chat, auth, users

# Configuration
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

# Initialize the FastAPI application
app = FastAPI()

# Define allowed origins for CORS
allowed_origins = ['*']

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
# Include all routers with the global prefix
app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
app.include_router(chat.router, prefix=API_PREFIX, tags=["Chat"])
app.include_router(auth.router, prefix=API_PREFIX, tags=["Authentication"])
app.include_router(users.router, prefix=API_PREFIX, tags=["Users"])