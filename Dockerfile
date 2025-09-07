# --- Stage 1: Build React Frontend (Builder Stage) ---
# Use the official Node.js 22 LTS (Long-Term Support) image.
FROM node:22-alpine AS builder

# Set the working directory within the builder stage.
WORKDIR /app/frontend

# Copy package manifests and install dependencies first to leverage Docker's layer caching.
COPY frontend/package*.json ./
RUN npm install

# Copy the rest of the frontend source code and build the application.
COPY frontend/ ./
RUN npm run build


# --- Stage 2: Final Production Image ---
# Use a slim, secure, and stable Python base image.
FROM python:3.12-slim

# Set recommended environment variables for running Python in a container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory for the final application.
WORKDIR /app

# Install Python dependencies efficiently.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend Python application code to the correct location.
COPY ./backend/app ./app

# Copy the compiled static frontend assets from the 'builder' stage.
COPY --from=builder /app/frontend/build ./static

# Expose the port the application will listen on.
EXPOSE 8000

# The command to start the Uvicorn ASGI server for FastAPI.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]