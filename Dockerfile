# Use a slim, secure, and stable Python base image.
FROM public.ecr.aws/docker/library/python:3.12-slim AS final

# Set recommended environment variables for running Python in a container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory for the final application.
WORKDIR /app

# Install Python dependencies efficiently.
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy the backend Python application code to the correct location.
COPY ./backend/app ./app
COPY ./backend/langgraph.json ./langgraph.json

# Expose the ports the application will listen on.
EXPOSE 8000 2024

# The command to start the Uvicorn ASGI server for FastAPI.
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["python", "backend/test_config.py"]
