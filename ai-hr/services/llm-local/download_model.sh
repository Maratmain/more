#!/bin/bash

# Model Download Script for LLM Local Service
# Downloads Qwen2.5-7B-Instruct GGUF models from Hugging Face

set -e

# Load environment variables
if [ -f /app/.env ]; then
    export $(cat /app/.env | grep -v '^#' | xargs)
fi

# Default values
LLM_MODEL=${LLM_MODEL:-Qwen2.5-7B-Instruct-Q5_K_M.gguf}
LLM_MODEL_URL=${LLM_MODEL_URL:-https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf}
LLM_DOWNLOAD_TIMEOUT=${LLM_DOWNLOAD_TIMEOUT:-3600}
LLM_DOWNLOAD_RETRIES=${LLM_DOWNLOAD_RETRIES:-3}

# Model path
MODEL_PATH="/app/models/${LLM_MODEL}"

echo "📥 Model Download Script"
echo "========================"
echo "Model: ${LLM_MODEL}"
echo "URL: ${LLM_MODEL_URL}"
echo "Path: ${MODEL_PATH}"
echo ""

# Create models directory
mkdir -p /app/models

# Check if model already exists
if [ -f "${MODEL_PATH}" ]; then
    echo "✅ Model already exists: ${MODEL_PATH}"
    MODEL_SIZE=$(du -h "${MODEL_PATH}" | cut -f1)
    echo "📊 Model size: ${MODEL_SIZE}"
    exit 0
fi

# Download model with retries
echo "🔄 Starting download..."
for attempt in $(seq 1 ${LLM_DOWNLOAD_RETRIES}); do
    echo "Attempt ${attempt}/${LLM_DOWNLOAD_RETRIES}"
    
    if wget --timeout=${LLM_DOWNLOAD_TIMEOUT} -O "${MODEL_PATH}" "${LLM_MODEL_URL}"; then
        echo "✅ Download successful!"
        break
    else
        echo "❌ Download failed (attempt ${attempt})"
        if [ ${attempt} -lt ${LLM_DOWNLOAD_RETRIES} ]; then
            echo "🔄 Retrying in 5 seconds..."
            sleep 5
        else
            echo "❌ All download attempts failed"
            exit 1
        fi
    fi
done

# Verify download
if [ -f "${MODEL_PATH}" ]; then
    MODEL_SIZE=$(du -h "${MODEL_PATH}" | cut -f1)
    echo "✅ Model downloaded successfully!"
    echo "📊 Model size: ${MODEL_SIZE}"
    echo "📍 Location: ${MODEL_PATH}"
else
    echo "❌ Model file not found after download"
    exit 1
fi

# Optional: Verify checksum if provided
if [ -n "${LLM_MODEL_CHECKSUM}" ] && [ "${LLM_MODEL_CHECKSUM}" != "sha256:auto" ]; then
    echo "🔍 Verifying checksum..."
    if echo "${LLM_MODEL_CHECKSUM}" | sha256sum -c -; then
        echo "✅ Checksum verified"
    else
        echo "❌ Checksum verification failed"
        exit 1
    fi
fi

echo "🎉 Model download completed successfully!"
