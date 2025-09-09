FROM ubuntu:22.04

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создание директории для моделей
RUN mkdir -p /models

# Копирование скрипта запуска
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Скачивание llama.cpp
RUN wget -O /tmp/llama.cpp.tar.gz https://github.com/ggerganov/llama.cpp/archive/refs/heads/master.tar.gz && \
    cd /tmp && tar -xzf llama.cpp.tar.gz && \
    cd llama.cpp-master && \
    make -j$(nproc) && \
    cp llama-server /usr/local/bin/ && \
    rm -rf /tmp/llama.cpp*

EXPOSE 8080

WORKDIR /models

CMD ["/run.sh"]