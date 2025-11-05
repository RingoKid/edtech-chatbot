# VS Code Setup Guide

This guide will help you set up VS Code for the best development experience with this project.

## Quick Start

### Option 1: Dev Containers (Recommended for Docker users)

If you're using Docker and have the Dev Containers extension installed:

1. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open the project in VS Code
3. When prompted, click "Reopen in Container" (or press F1 and select "Dev Containers: Reopen in Container")
4. VS Code will rebuild and connect to your Docker container
5. All Python imports will be resolved automatically

### Option 2: Local Development (without Dev Containers)

If you prefer working outside of containers but still using Docker for services:

1. Make sure Docker is running
2. Start your containers: `docker-compose up -d`
3. Reload VS Code window (F1 → "Developer: Reload Window")
4. Python imports should now be resolved correctly

The `.vscode/settings.json` has been configured to:
- Point to the correct Python interpreter
- Set up proper PYTHONPATH for the backend
- Configure Pylance to index langchain and langgraph packages
- Enable pytest for testing

## Required Extensions

The following extensions are recommended for this project:

- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Python Debugger** (ms-python.debugpy)
- **Docker** (ms-azuretools.vscode-docker)
- **Prettier** (esbenp.prettier-vscode)
- **ESLint** (dbaeumer.vscode-eslint)
- **Dev Containers** (ms-vscode-remote.remote-containers) - Optional but recommended

## Debugging

### Backend Debugging

Two debug configurations are available:

1. **Backend: Attach to Docker** - Automatically starts Docker Compose and attaches the debugger
2. **Backend: Attach Manual (No PreLaunch)** - Attach to an already running container

### Full Stack Debugging

Use the **Full-Stack Debug (Docker)** compound configuration to debug both backend and frontend simultaneously.

## Troubleshooting

### Import warnings still showing

1. Reload the VS Code window (F1 → "Developer: Reload Window")
2. If using Dev Containers, make sure you've reopened in the container
3. Check that Docker containers are running: `docker-compose ps`
4. Verify PYTHONPATH is set in the terminal: `echo $PYTHONPATH`

### Python interpreter not found

1. Make sure Docker containers are running
2. If using Dev Containers, ensure you're connected to the container (check the bottom-left corner of VS Code)
3. Manually select the Python interpreter: F1 → "Python: Select Interpreter"

### Tests not discovered

1. Ensure pytest is installed in your environment
2. Check the Output panel → Python Test Log for errors
3. Verify the test path in settings: `backend/tests`

## Project Structure

```
.
├── backend/          # Python FastAPI backend
│   ├── app/         # Application code
│   └── tests/       # Test files
├── frontend/        # React frontend
│   └── src/         # Source files
├── .devcontainer/   # Dev Container configuration
└── .vscode/         # VS Code settings and launch configurations
```

## Additional Resources

- [Dev Containers documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Python in VS Code](https://code.visualstudio.com/docs/python/python-tutorial)
- [Docker Compose](https://docs.docker.com/compose/)
