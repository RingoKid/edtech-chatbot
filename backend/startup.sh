#!/bin/bash
set -e

echo "🚀 Starting EdTech Chatbot Backend..."

# Function to wait for DynamoDB to be ready
wait_for_dynamodb() {
    echo "⏳ Waiting for DynamoDB to be ready..."
    until python -c "
import sys
sys.path.append('/app')
from app.database import test_connection

for attempt in range(30):
    try:
        if test_connection():
            print('✅ DynamoDB is ready!')
            sys.exit(0)
    except Exception as e:
        print(f'Attempt {attempt + 1}/30: DynamoDB not ready yet - {e}')
        import time
        time.sleep(2)

print('❌ DynamoDB failed to become ready after 60 seconds')
sys.exit(1)
"; do
        echo "⏳ DynamoDB is unavailable - sleeping..."
        sleep 2
    done
}

# Function to load forms into database
load_forms() {
    echo "📚 Loading educational forms into DynamoDB..."

    if python load_forms.py; then
        echo "✅ Educational forms loaded successfully!"
    else
        echo "⚠️ Failed to load forms, but continuing startup..."
        echo "💡 You can manually load forms later with: docker-compose exec backend python load_forms.py"
    fi
}

# Function to start services
start_services() {
    echo "🔧 Starting FastAPI and LangGraph Studio..."

    # Start LangGraph Studio in background
    echo "🧠 Starting LangGraph Studio on port 2024..."
    langgraph dev --host 0.0.0.0 --port 2024 &
    LANGGRAPH_PID=$!

    # Give LangGraph a moment to start
    sleep 3

    # Start FastAPI server
    echo "🌐 Starting FastAPI server on port 8000..."
    if [ "$DEBUG_MODE" = "true" ]; then
        echo "🐛 Starting FastAPI with debugger on port 5678..."
        python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    else
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    fi
    FASTAPI_PID=$!

    # Function to handle shutdown gracefully
    shutdown() {
        echo "🛑 Shutting down services..."
        kill $LANGGRAPH_PID 2>/dev/null || true
        kill $FASTAPI_PID 2>/dev/null || true
        wait $LANGGRAPH_PID 2>/dev/null || true
        wait $FASTAPI_PID 2>/dev/null || true
        echo "👋 Shutdown complete"
        exit 0
    }

    # Set up signal handlers
    trap shutdown SIGTERM SIGINT

    # Wait for both processes
    wait
}

# Main execution flow
main() {
    echo "=================================="
    echo "  EdTech Chatbot Backend Startup  "
    echo "=================================="

    # Wait for database
    wait_for_dynamodb

    # Load forms automatically
    load_forms

    echo "🎉 Initialization complete! Starting services..."
    echo "📍 FastAPI: http://localhost:8000"
    echo "📍 LangGraph Studio: http://localhost:2024"
    echo "=================================="

    # Start all services
    start_services
}

# Run main function
main