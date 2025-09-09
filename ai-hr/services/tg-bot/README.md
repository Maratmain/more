# Telegram Bot Service

Telegram bot for CV upload and processing in the AI-HR system.

## Features

- **Document Upload**: Accept PDF, DOCX, DOC, TXT files
- **File Validation**: Size and type checking
- **CV Processing**: Forward files to CV processing service
- **User Feedback**: Status updates and error handling
- **Large File Support**: Integration with Local Bot API for files >20MB

## Configuration

### Environment Variables

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional
TELEGRAM_USE_LOCAL_BOT_API=false
TELEGRAM_BOT_API_URL=http://localhost:8081
CV_SERVICE_URL=http://cv:8007
MAX_FILE_SIZE_MB=20
```

### Bot Token Setup

1. **Create Bot**: Message [@BotFather](https://t.me/BotFather) on Telegram
2. **Get Token**: Use `/newbot` command and follow instructions
3. **Configure**: Add token to `.env` file

```bash
# Example .env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

## Limits & Large Files

### Standard Bot API Limits

The default Telegram Bot API has strict limitations for file operations:

- **Download limit**: ~20MB via `getFile` method
- **Upload limit**: ~50MB via `sendDocument` method
- **Download timeout**: 60 seconds  
- **Rate limits**: 30 requests per second
- **Hard limit**: Cannot be bypassed with standard Bot API

**References**: 
- [Telegram Bot API FAQ](https://core.telegram.org/bots/faq#what-files-can-i-download-using-bots)
- [Telegram Bot PHP SDK](https://github.com/irazasyed/telegram-bot-sdk)
- [Telegram Core Documentation](https://core.telegram.org/bots/api#getfile)

### Local Bot API Server

The Local Bot API Server removes download limits and provides enhanced upload capabilities:

- **Download limit**: Removed (can download any file size)
- **Upload limit**: Up to 2000MB via `sendDocument`
- **Performance**: Better latency and throughput
- **Official support**: Documented in Bot API documentation

**Setup**:
```bash
# Enable Local Bot API
TELEGRAM_USE_LOCAL_BOT_API=true
TELEGRAM_BOT_API_URL=http://bot-api:8081
```

**References**:
- [Telegram Core - Local Bot API](https://core.telegram.org/bots/api#using-a-local-bot-api-server)

### MTProto Alternative

For advanced use cases with very large files, MTProto clients can be used:

- **Telethon**: Python MTProto client
- **Pyrogram**: Modern Python MTProto client
- **File size**: No practical limits
- **Complexity**: Requires more setup and maintenance

**References**:
- [Stack Overflow - Large File Uploads](https://stackoverflow.com/questions/tagged/telegram+mtproto)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Pyrogram Documentation](https://docs.pyrogram.org/)

### File Size Warning System

The bot includes intelligent file size warnings:

- **18-20 MB**: Warning about approaching limit with recommendations
- **>20 MB**: Clear error with alternative solutions
- **Dynamic limits**: Adjusts based on Bot API type (Standard vs Local)

### Solutions for Large Files

#### 1. Local Bot API Server (Recommended)

For files >20MB, use a local Bot API server:

```bash
# Install and run local Bot API server
docker run -d \
  --name telegram-bot-api \
  -p 8081:8081 \
  -v telegram-data:/var/lib/telegram-bot-api \
  telegram-bot-api:latest \
  --api-id=YOUR_API_ID \
  --api-hash=YOUR_API_HASH \
  --local
```

**Configuration**:
```bash
TELEGRAM_USE_LOCAL_BOT_API=true
TELEGRAM_BOT_API_URL=http://localhost:8081
```

**Benefits**:
- **No file size limits** (up to 2GB)
- **Faster downloads** (local network)
- **Better reliability** (no rate limits)
- **Full control** over API behavior

**Reference**: [Telegram Core Documentation](https://core.telegram.org/bots/api#using-a-local-bot-api-server)

#### 2. MTProto Clients (Alternative)

For advanced use cases, consider MTProto clients:

- **Telethon**: Python async MTProto client
- **Pyrogram**: Modern Python MTProto client

**Example with Telethon**:
```python
from telethon import TelegramClient

client = TelegramClient('session', api_id, api_hash)
# No file size limits with MTProto
```

**Benefits**:
- **No file size limits** (up to 2GB)
- **Direct MTProto access** (bypasses Bot API)
- **Advanced features** (channels, groups, etc.)
- **Custom implementations** possible

**References**:
- [Telethon GitHub](https://github.com/LonamiWebs/Telethon)
- [Pyrogram GitHub](https://github.com/pyrogram/pyrogram)

#### 3. Web Interface (Fallback)

For very large files or when Bot API is not suitable:

- **Admin UI**: Use the web interface at `http://localhost:8080`
- **Direct API**: Upload via `POST /ingest` endpoint
- **File compression**: Reduce PDF size before upload

## Usage

### Start Bot

```bash
# Using Docker Compose
docker compose up tg-bot

# Or manually
cd services/tg-bot
pip install -r requirements.txt
python main.py
```

### Bot Commands

- `/start` - Welcome message and instructions
- `/upload_cv` - Upload CV with detailed guidance
- `/help` - Show available commands and usage
- `/status` - Check AI-HR service status

### Command Examples

#### `/start`
Shows welcome message with current configuration:
```
🤖 AI-HR CV Processing Bot

Привет! Я помогу обработать ваше резюме для системы AI-HR.

📋 Поддерживаемые форматы:
• PDF (.pdf)
• Word документы (.docx, .doc)
• Текстовые файлы (.txt)

⚠️ Ограничения:
• Максимальный размер файла: 2000 MB
• Используется: Local Bot API
```

#### `/upload_cv`
Provides detailed upload guidance:
```
📤 Загрузка резюме

Отправьте файл резюме в чат для обработки.

📏 Ограничения размера:
• Текущий лимит: 2000 MB
• API: Local Bot API

💡 Альтернативы для больших файлов:
• Local Bot API сервер
• MTProto клиенты (Telethon/Pyrogram)
• Веб-интерфейс AI-HR
```

#### `/status`
Checks AI-HR service health:
```
✅ Сервис AI-HR активен

🔧 Статус:
• CV Service: ok
• Embedder: sentence-transformers/all-MiniLM-L6-v2
• Qdrant: connected
• Collection: cv_chunks

📊 Готов к обработке резюме
```

### File Upload

1. **Send Document**: Upload PDF/DOCX file to bot
2. **Validation**: Bot checks file size and type
3. **Processing**: File forwarded to CV service
4. **Confirmation**: User receives status update

### File Size Warnings

#### Warning for 18-20 MB files (Standard Bot API)
```
⚠️ Файл близок к лимиту

Размер: 19.2 MB
Лимит Standard Bot API: 20 MB

💡 Рекомендации:
• Попробуйте сжать PDF
• Используйте Local Bot API сервер
• Альтернатива: MTProto клиенты (Telethon/Pyrogram)
• Веб-интерфейс AI-HR

🔧 Настройка Local Bot API:
TELEGRAM_USE_LOCAL_BOT_API=true
TELEGRAM_BOT_API_URL=http://localhost:8081
```

#### Error for >20 MB files (Standard Bot API)
```
❌ Файл слишком большой

Размер: 25.3 MB
Максимум (Standard Bot API): 20 MB

💡 Альтернативы:
• Local Bot API сервер (до 2000 MB)
• MTProto клиенты (Telethon/Pyrogram)
• Веб-интерфейс AI-HR
```

## API Integration

### CV Service Communication

The bot forwards uploaded files to the CV processing service:

```python
# POST to CV service
files = {'file': (filename, file_content, content_type)}
response = requests.post(f"{CV_SERVICE_URL}/ingest", files=files)
```

### Error Handling

- **File too large**: Suggest using web interface
- **Unsupported format**: List supported formats
- **Service unavailable**: Retry mechanism
- **Processing failed**: Detailed error message

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN=your_token
export CV_SERVICE_URL=http://localhost:8007

# Run bot
python main.py
```

### Testing

```bash
# Test file upload
curl -X POST "http://localhost:8007/ingest" \
  -F "file=@test_cv.pdf"

# Check bot status
curl "http://localhost:8007/health"
```

## Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check token validity
   - Verify network connectivity
   - Check service logs

2. **File upload fails**:
   - Verify file size <20MB (or use Local Bot API)
   - Check supported file formats
   - Ensure CV service is running

3. **Large file issues**:
   - Enable Local Bot API server
   - Consider MTProto clients
   - Use web interface as fallback

### Logs

```bash
# View bot logs
docker logs ai-hr-tg-bot-1 -f

# Check CV service logs
docker logs ai-hr-cv-1 -f
```

## Security

- **Token Security**: Never commit tokens to version control
- **File Validation**: Strict file type and size checking
- **Rate Limiting**: Built-in rate limiting for API calls
- **Error Handling**: No sensitive information in error messages

## Monitoring

- **Health Checks**: `/health` endpoint
- **Metrics**: Request count and success rate
- **Alerts**: Failed upload notifications
- **Logs**: Structured logging for debugging