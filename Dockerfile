# --- Stage 1: Build React Frontend (Builder Stage) ---
# Use the official Node.js 22 LTS (Long-Term Support) image.
FROM public.ecr.aws/docker/library/node:22-alpine AS builder

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
FROM public.ecr.aws/docker/library/python:3.12-slim AS final

# Set recommended environment variables for running Python in a container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory for the final application.
WORKDIR /app

# Install system dependencies including wget and unzip for AWS CLI
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN wget "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -O "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

RUN ln -sf /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws

# Install Python dependencies efficiently.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend Python application code to the correct location.
COPY ./backend/app ./app

# Copy the compiled static frontend assets from the 'builder' stage.
COPY --from=builder /app/frontend/dist ./static

# Expose the port the application will listen on.
EXPOSE 8000

# The command to start the Uvicorn ASGI server for FastAPI.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]