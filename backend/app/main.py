import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.routers import health, chat, auth, users
from app.config import settings
from app.routers import health, chat, auth, users, handwriting_bot
# Temporarily disable educational_bot due to LangGraph installation issue
# from app.routers import educational_bot

# Configuration
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

# Initialize LangSmith tracing
settings.initialize_langsmith()

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
app.include_router(handwriting_bot.router, prefix=API_PREFIX, tags=["Handwriting Bot"])
# Temporarily disable educational_bot router due to LangGraph installation issue
# app.include_router(educational_bot.router, prefix=API_PREFIX, tags=["Educational Bot"])


# --- Static File Serving ---
# This section serves the compiled React frontend.

# Define the path to the static files directory built by React.
# The path is relative to this main.py file.
STATIC_FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

# Only set up static file serving if the static directory exists (production mode)
if os.path.exists(STATIC_FILES_DIR) and os.path.exists(os.path.join(STATIC_FILES_DIR, "static")):
    # Mount the 'static' sub-directory from the React build to the '/static' URL path.
    # This is for serving assets like CSS, JavaScript, and images.
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(STATIC_FILES_DIR, "static")),
        name="static_assets"
    )

    # A catch-all endpoint to serve the 'index.html' of the React app.
    # This is critical for Single-Page Applications (SPAs) that use client-side routing.
    # It ensures that any path not matched by your API routes will load the React app.
    @app.get("/{full_path:path}", response_class=FileResponse)
    async def serve_react_app(full_path: str):
        """
        Serves the main index.html file for any non-API route.
        """
        return FileResponse(os.path.join(STATIC_FILES_DIR, "index.html"))