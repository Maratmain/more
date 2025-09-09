#!/bin/bash

# LLM Gateway Service - curl Examples
# This script demonstrates how to use the LLM Gateway service with curl

BASE_URL="http://localhost:8008"

echo "🚀 LLM Gateway Service - curl Examples"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}🔍 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test 1: Health Check
print_step "Testing health endpoint"
curl -s -X GET "${BASE_URL}/health" | jq '.' || print_error "Health check failed"
echo ""

# Test 2: List Models
print_step "Testing models endpoint"
curl -s -X GET "${BASE_URL}/models" | jq '.' || print_error "Models endpoint failed"
echo ""

# Test 3: Generate with OpenRouter (if API key is set)
if [ -n "$OPENROUTER_API_KEY" ]; then
    print_step "Testing OpenRouter generation"
    curl -s -X POST "${BASE_URL}/generate" \
        -H "Content-Type: application/json" \
        -d '{
            "system": "You are a helpful AI assistant for HR interviews.",
            "prompt": "What are the key skills for a Python developer?",
            "model": "env_default",
            "stream": false,
            "max_tokens": 100,
            "temperature": 0.7
        }' | jq '.' || print_error "OpenRouter generation failed"
    echo ""
else
    print_warning "Skipping OpenRouter test - OPENROUTER_API_KEY not set"
fi

# Test 4: Generate with OpenAI-compatible (Ollama example)
print_step "Testing OpenAI-compatible generation (Ollama)"
curl -s -X POST "${BASE_URL}/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "system": "You are a helpful AI assistant.",
        "prompt": "Hello, how are you?",
        "model": "env_default",
        "stream": false,
        "max_tokens": 50,
        "temperature": 0.7
    }' | jq '.' || print_error "OpenAI-compatible generation failed"
echo ""

# Test 5: Streaming generation
print_step "Testing streaming generation"
curl -s -X POST "${BASE_URL}/generate/stream" \
    -H "Content-Type: application/json" \
    -d '{
        "system": "You are a helpful AI assistant.",
        "prompt": "Count from 1 to 5, one number per line.",
        "model": "env_default",
        "stream": true,
        "max_tokens": 50,
        "temperature": 0.7
    }' || print_error "Streaming generation failed"
echo ""

# Test 6: Error handling - invalid model
print_step "Testing error handling (invalid model)"
curl -s -X POST "${BASE_URL}/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "system": "You are a helpful AI assistant.",
        "prompt": "Hello",
        "model": "invalid-model",
        "stream": false
    }' | jq '.' || print_error "Error handling test failed"
echo ""

# Test 7: Error handling - missing prompt
print_step "Testing error handling (missing prompt)"
curl -s -X POST "${BASE_URL}/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "system": "You are a helpful AI assistant.",
        "model": "env_default",
        "stream": false
    }' | jq '.' || print_error "Error handling test failed"
echo ""

print_success "All curl examples completed!"
echo ""
echo "📝 Usage Notes:"
echo "  - Set OPENROUTER_API_KEY environment variable for OpenRouter tests"
echo "  - Ensure OpenAI-compatible service (like Ollama) is running for local tests"
echo "  - Check service logs if any tests fail"
echo "  - Use 'jq' for pretty JSON output (install with: apt-get install jq)"
