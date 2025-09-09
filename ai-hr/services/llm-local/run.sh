#!/bin/bash

set -e

echo "🚀 Запуск LLM локального сервиса..."

# Переменные окружения
MODEL_URL=${LLM_MODEL_URL:-"https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf"}
MODEL_NAME=${LLM_MODEL:-"Qwen2.5-7B-Instruct-Q5_K_M.gguf"}
PORT=${LLM_PORT:-8080}
CTX=${LLM_CTX:-8192}
THREADS=${LLM_THREADS:-8}

MODEL_PATH="/models/${MODEL_NAME}"

# Проверка наличия модели
if [ ! -f "$MODEL_PATH" ]; then
    echo "📥 Скачивание модели: $MODEL_NAME"
    echo "URL: $MODEL_URL"
    
    wget -O "$MODEL_PATH" "$MODEL_URL" || {
        echo "❌ Ошибка скачивания модели"
        exit 1
    }
    
    echo "✅ Модель скачана: $MODEL_PATH"
else
    echo "✅ Модель уже существует: $MODEL_PATH"
fi

# Проверка размера модели
MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
echo "📊 Размер модели: $MODEL_SIZE"

# Запуск llama-server
echo "🎯 Запуск llama-server..."
echo "Порт: $PORT"
echo "Контекст: $CTX"
echo "Потоки: $THREADS"

llama-server \
    -m "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port "$PORT" \
    -c "$CTX" \
    --parallel 4 \
    --embedding \
    --api-server \
    --threads "$THREADS" \
    --log-format json \
    --verbose