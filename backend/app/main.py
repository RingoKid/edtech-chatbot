import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Initialize the FastAPI application
app = FastAPI()

# --- API Endpoints ---
# This is where your business logic and API routes will go.
# We'll start with a simple health check.

@app.get("/api/v1/health")
def read_health():
    """
    Health check endpoint to confirm the API is running.
    """
    return {"status": "ok"}


@app.get("/api/v1/debug-test")
def debug_test():
    """
    Test endpoint for debugging - set a breakpoint here!
    """
    message = "This is a debug test endpoint"
    data = {
        "message": message,
        "timestamp": "2025-09-08",
        "debug": True
    }
    # Set a breakpoint on the next line to test debugging
    result = {"status": "debug-success", "data": data}
    return result


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