# Руководство по развертыванию AI-HR

## Обзор системы

AI-HR - это полнофункциональная система для проведения интервью с использованием искусственного интеллекта, включающая:

- **Real-time коммуникации** через LiveKit с TURN сервером
- **HTTPS фронтенд** с автоматическими сертификатами через Caddy
- **Локальная LLM** модель Qwen2.5-7B через llama.cpp
- **Telegram бот** с поддержкой больших файлов (до 2GB)
- **AI сервисы**: ASR, TTS, DM, CV обработка, отчеты, метрики

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Caddy Proxy   │    │   LiveKit       │    │   LLM Local     │
│   (HTTPS/TLS)   │    │   (WebRTC/TURN) │    │   (llama.cpp)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Realtime       │    │  Token Server   │    │  Dialog Manager │
│  Client         │    │  (JWT tokens)   │    │  (AI responses) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Telegram Bot   │    │  AI Services    │    │  Vector DB      │
│  (Local API)    │    │  (ASR/TTS/CV)   │    │  (Qdrant)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Требования

### Системные требования
- **CPU**: 8+ ядер (для LLM)
- **RAM**: 16+ GB (для модели Qwen2.5-7B)
- **Диск**: 50+ GB (модель ~4GB + данные)
- **Сеть**: Публичный IP с открытыми портами

### Порты
- **80/443**: HTTP/HTTPS (Caddy)
- **7880/7881**: LiveKit WebRTC
- **3478/5349**: TURN сервер
- **50000-60000**: RTC порты
- **8080**: LLM сервер
- **3000**: Token сервер
- **8001-8007**: AI сервисы

## Пошаговое развертывание

### 1. Подготовка сервера

```bash
# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Клонирование репозитория
git clone <repository-url>
cd ai-hr
```

### 2. Настройка DNS

Создайте DNS записи:
```
app.your-domain.com    A    YOUR_PUBLIC_IP
video.your-domain.com  A    YOUR_PUBLIC_IP
```

### 3. Конфигурация

```bash
# Копирование и настройка переменных
cp env.example .env

# Редактирование .env
nano .env
```

**Обязательные переменные:**
```bash
DOMAIN=your-domain.com
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMINS=your_telegram_id
```

### 4. Настройка LiveKit

```bash
# Редактирование конфигурации LiveKit
nano deploy/livekit.yaml

# Замените домен в конфигурации
sed -i 's/video.your-domain.com/video.${DOMAIN}/g' deploy/livekit.yaml
```

### 5. Настройка Caddy

```bash
# Редактирование Caddyfile
nano deploy/Caddyfile

# Замените домены
sed -i 's/your-domain.com/${DOMAIN}/g' deploy/Caddyfile
```

### 6. Запуск сервисов

```bash
# Основные сервисы
docker compose up -d livekit caddy llm-local token-server realtime-client

# Ожидание готовности LLM (скачивание модели)
docker compose logs -f llm-local

# AI сервисы
docker compose up -d api report asr tts dm cv metrics

# Telegram бот
docker compose up -d bot-api tg-bot
```

### 7. Проверка работоспособности

```bash
# Проверка HTTPS
curl -I https://app.${DOMAIN}/

# Проверка токен-сервера
curl https://app.${DOMAIN}/api/health

# Проверка генерации токена
curl "https://app.${DOMAIN}/api/token?identity=test&room=demo"

# Проверка контейнеров
docker compose ps
```

## Тестирование

### 1. Первый звонок

1. Откройте: `https://app.${DOMAIN}/?room=demo&name=Я`
2. Пригласите участника: `https://app.${DOMAIN}/?room=demo&name=Кандидат`
3. Разрешите доступ к камере/микрофону
4. Проверьте видео/аудио связь
5. Протестируйте AI ответы

### 2. Telegram бот

1. Найдите бота в Telegram
2. Отправьте `/start`
3. Загрузите резюме (PDF/DOCX)
4. Проверьте админ команды: `/admin`

## Мониторинг

### Логи сервисов
```bash
# Основные сервисы
docker compose logs -f livekit
docker compose logs -f caddy
docker compose logs -f llm-local

# AI сервисы
docker compose logs -f dm
docker compose logs -f asr
docker compose logs -f tts

# Telegram бот
docker compose logs -f tg-bot
```

### Метрики
```bash
# Проверка метрик
curl http://localhost:8006/metrics

# Статус сервисов
curl http://localhost:8001/health
curl http://localhost:8007/health
```

## Troubleshooting

### Проблемы с медиа
- **Нет звука/видео**: проверьте TURN сервер и порты
- **CORS ошибки**: проверьте CORS_ORIGIN в .env
- **HTTPS обязателен**: браузеры требуют HTTPS для медиа

### Проблемы с LLM
- **Медленные ответы**: увеличьте LLM_THREADS
- **Ошибки JSON**: проверьте LLM_JSON_SCHEMA_ENFORCE
- **Нехватка памяти**: уменьшите LLM_CTX

### Проблемы с ботом
- **Большие файлы**: убедитесь что TELEGRAM_USE_LOCAL_BOT_API=true
- **Нет доступа**: проверьте TELEGRAM_ADMINS
- **Ошибки API**: проверьте TELEGRAM_BOT_TOKEN

## Безопасность

### Рекомендации
- Используйте сильные пароли для API ключей
- Ограничьте доступ к админ функциям
- Регулярно обновляйте Docker образы
- Мониторьте логи на подозрительную активность

### Firewall
```bash
# Открыть только необходимые порты
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3478/udp
ufw allow 50000:60000/udp
ufw enable
```

## Масштабирование

### Горизонтальное масштабирование
- Добавьте балансировщик нагрузки перед Caddy
- Используйте внешнюю БД (PostgreSQL/Redis)
- Разверните несколько инстансов AI сервисов

### Вертикальное масштабирование
- Увеличьте ресурсы сервера
- Добавьте GPU для ускорения LLM
- Используйте SSD для быстрого доступа к данным

## Поддержка

При возникновении проблем:
1. Проверьте логи сервисов
2. Убедитесь в правильности конфигурации
3. Проверьте доступность портов
4. Обратитесь к документации LiveKit и llama.cpp
