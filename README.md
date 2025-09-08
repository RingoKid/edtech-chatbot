# EdTech Chatbot

A full-stack education technology chatbot application built with FastAPI (Python) backend and React frontend, containerized with Docker for easy development and deployment.

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.12) with Uvicorn ASGI server
- **Frontend**: React 19 with Node.js 22
- **Containerization**: Docker with multi-stage builds
- **Development**: Hot-reloading enabled for both frontend and backend
- **Debugging**: VS Code debugger support with debugpy

## 🔄 Development Workflow & Branch Management

### Branch Management Rules

- **main branch**: For production releases only (protected - requires pull request)
- **develop branch**: For sandbox and testing (protected - requires pull request)
- **Feature branches**: Must be created from the develop branch

### Development Workflow

1. Create a feature branch from develop: `git checkout develop && git checkout -b feature-name`
2. Make your changes and test using the Docker development environment
3. Update your feature branch with the latest develop branch before creating a pull request
4. Create a pull request to merge into develop
5. All pull requests require a review before merging
6. All changes to main and develop branches must be made through pull requests

## 📋 Prerequisites

Before running this project, make sure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/) (version 20.10 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0 or higher)

## 🚀 Quick Start

### Development Mode

1. **Clone the repository:**

   ```bash
   git clone https://github.com/RingoKid/edtech-chatbot
   cd edtech-chatbot
   ```

2. **Start the development environment:**

   ```bash
   docker-compose up --build
   ```

   This command will:
   - Build the backend Docker image
   - Start the FastAPI backend on `http://localhost:8000`
   - Start the React frontend on `http://localhost:3000`
   - Enable hot-reloading for both services

3. **Access the application:**
   - Frontend: <http://localhost:3000>
   - Backend API: <http://localhost:8000>

### Debug Mode

For debugging with VS Code and breakpoints, you can use the VS Code debugger which is already configured to automatically start the debug containers.

1. **Launch VS Code debugger:**
   - Open the project in VS Code
   - Go to Run and Debug (Ctrl+Shift+D)
   - Select "Backend: Attach to Docker" or "Full-Stack Debug (Docker)"
   - Press F5 to start debugging

## 🐳 Docker Commands Reference

### Basic Operations

```bash
# Start all services
docker-compose up

# Start services in detached mode (background)
docker-compose up -d

# Build and start services
docker-compose up --build

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Development Commands

```bash
# Start development environment with hot-reloading
docker-compose up --build

# Start debug environment
docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build -d

# View logs
docker-compose logs

# View logs for specific service
docker-compose logs backend
docker-compose logs frontend

# Restart a specific service
docker-compose restart backend
```

### Debugging Commands

```bash
# Start with debug configuration
docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build -d

# Check if debugger port is available
docker-compose ps

# Access backend container shell
docker-compose exec backend bash

# Access frontend container shell
docker-compose exec frontend sh
```

## 📁 Project Structure

```text
edtech-chatbot/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py            # FastAPI application entry point
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React frontend
│   ├── public/               # Static assets
│   ├── src/                  # React source code
│   └── package.json          # Node.js dependencies
├── .vscode/                  # VS Code configuration
│   ├── launch.json           # Debug configurations
│   └── tasks.json            # Build tasks
├── Dockerfile                # Multi-stage Docker build
├── docker-compose.yml        # Development configuration
├── docker-compose.override.yml # Debug configuration
└── README.md                 # This file
```

## 🔧 Configuration

### Ports

- **Frontend**: 3000 (React development server)
- **Backend**: 8000 (FastAPI server)
- **Debugger**: 5678 (Python debugpy - debug mode only)

### Volumes

- Backend source code is mounted for hot-reloading: `./backend:/app`
- Frontend source code is mounted for hot-reloading: `./frontend:/app/frontend`
- Node modules are stored in a named volume for performance: `node_modules`

## 🐛 Debugging

### VS Code Setup

1. Install the Python extension for VS Code
2. Use the provided launch configurations:
   - **Backend: Attach to Docker** - Attaches to the backend container with pre-launch task
   - **Backend: Attach Manual** - Manual attach without starting containers
   - **Frontend: Launch Chrome** - Debugs frontend in Chrome
   - **Full-Stack Debug** - Debugs both frontend and backend simultaneously

### Debugging Steps

1. Use the VS Code debugger with the provided launch configurations
2. Set breakpoints in your Python code
3. Launch the debugger in VS Code (F5)
4. The debugger will automatically start the containers and attach

## 🛠️ Development Workflow

1. **Make changes** to your code (backend or frontend)
2. **Changes are automatically reflected** due to volume mounts and hot-reloading
3. **For backend changes**: Uvicorn will automatically restart the server
4. **For frontend changes**: React development server will hot-reload
5. **No need to rebuild** containers unless you change dependencies

## 📝 Adding Dependencies

### Backend (Python)

1. Add packages to `backend/requirements.txt`
2. Rebuild the container: `docker-compose up --build backend`

### Frontend (Node.js)

1. The container will automatically install new packages from `package.json`
2. Or run: `docker-compose exec frontend npm install <package-name>`
