# Use a slim, secure, and stable Python base image.
FROM public.ecr.aws/docker/library/python:3.12-slim AS final

# Set recommended environment variables for running Python in a container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install Git and other essential tools for dev container
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*


# Copy the backend Python application code to the correct location.
COPY ./backend/app ./app
COPY ./backend/langgraph.json ./langgraph.json

# Expose the ports the application will listen on.
EXPOSE 8000 2024

# The command to start the Uvicorn ASGI server for FastAPI.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]