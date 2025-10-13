#!/bin/bash

# LangSmith Test Runner Script for Educational Chatbot
# This script sets up the environment and runs comprehensive tests

echo "🚀 Educational Chatbot LangSmith Test Suite"
echo "=========================================="

# Check if we're in the backend directory
if [[ ! -f "test_langsmith_flow.py" ]]; then
    echo "❌ Error: Must be run from the backend directory"
    echo "📁 Current directory: $(pwd)"
    echo "💡 Run: cd backend && ./run_langsmith_tests.sh"
    exit 1
fi

# Check for required environment variables
echo "🔍 Checking environment configuration..."

if [[ -z "${OPENAI_API_KEY}" ]]; then
    echo "⚠️ Warning: OPENAI_API_KEY not set"
    echo "💡 Set with: export OPENAI_API_KEY='your-key-here'"
fi

if [[ -z "${LANGSMITH_API_KEY}" ]]; then
    echo "⚠️ Warning: LANGSMITH_API_KEY not set"
    echo "💡 Set with: export LANGSMITH_API_KEY='your-key-here'"
fi

if [[ -z "${LANGSMITH_PROJECT}" ]]; then
    echo "📝 Setting default LangSmith project name"
    export LANGSMITH_PROJECT="educational-chatbot-tests"
fi

# Set LangSmith tracing
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY="${LANGSMITH_API_KEY}"

echo "✅ Configuration:"
echo "   📊 LangSmith Project: ${LANGSMITH_PROJECT}"
echo "   🔍 Tracing Enabled: ${LANGCHAIN_TRACING_V2}"
echo "   🤖 OpenAI API: ${OPENAI_API_KEY:+configured}${OPENAI_API_KEY:-not set}"
echo "   📈 LangSmith API: ${LANGSMITH_API_KEY:+configured}${LANGSMITH_API_KEY:-not set}"

echo ""
echo "🧪 Starting LangSmith Tests..."
echo "=========================================="

# Run the comprehensive test suite
python3 test_langsmith_flow.py

# Check the exit code
if [[ $? -eq 0 ]]; then
    echo ""
    echo "✅ Tests completed successfully!"
    echo "📊 View detailed traces and visualizations:"
    echo "   🔗 LangSmith Dashboard: https://smith.langchain.com/"
    echo "   📈 Project: ${LANGSMITH_PROJECT}"
    echo "   🎯 LangGraph Studio: http://localhost:2024"
    echo ""
    echo "💡 To start LangGraph Studio:"
    echo "   docker-compose up -d"
    echo "   # Then navigate to http://localhost:2024"
else
    echo ""
    echo "❌ Tests failed with errors"
    echo "📝 Check the output above for details"
    exit 1
fi