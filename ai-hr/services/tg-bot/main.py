# Telegram Bot для AI-HR
import os
import asyncio
import tempfile
import requests
from pathlib import Path
from typing import Optional

from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CV_SERVICE_URL = os.getenv("CV_SERVICE_URL", "http://cv:8007")
REPORT_API_URL = os.getenv("REPORT_API_URL", "http://report:8005")
MAIN_API_URL = os.getenv("MAIN_API_URL", "http://api:8001")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "ai_hr_bot")

TELEGRAM_ADMINS = os.getenv("TELEGRAM_ADMINS", "").split(",")
TELEGRAM_ADMINS = [int(admin.strip()) for admin in TELEGRAM_ADMINS if admin.strip().isdigit()]

TELEGRAM_USE_LOCAL_BOT_API = os.getenv("TELEGRAM_USE_LOCAL_BOT_API", "false").lower() == "true"
TELEGRAM_BOT_API_URL = os.getenv("TELEGRAM_BOT_API_URL", "http://localhost:8081")

STANDARD_BOT_API_LIMIT_MB = 20
LOCAL_BOT_API_LIMIT_MB = 2000

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN обязателен")

SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}

def is_admin(user_id: int) -> bool:
    return user_id in TELEGRAM_ADMINS

def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with deep link support"""
    user_id = update.effective_user.id
    
    # Check for deep link parameter
    if context.args:
        deep_link = context.args[0]
        if deep_link.startswith("cand_"):
            candidate_id = deep_link[5:]  # Remove "cand_" prefix
            await handle_candidate_deep_link(update, candidate_id)
            return
    
    # Determine current file size limit
    current_limit = LOCAL_BOT_API_LIMIT_MB if TELEGRAM_USE_LOCAL_BOT_API else STANDARD_BOT_API_LIMIT_MB
    api_type = "Local Bot API" if TELEGRAM_USE_LOCAL_BOT_API else "Standard Bot API"
    
    # Check if user is admin
    admin_commands = ""
    if is_admin(user_id):
        admin_commands = """
🔧 *Админ команды:*
/admin - админ меню
/candidate <id> - карточка кандидата
/conferences - ссылки на конференции
"""
    
    welcome_message = f"""
🤖 *AI-HR CV Processing Bot*

Привет! Я помогу обработать ваше резюме для системы AI-HR.

📋 *Поддерживаемые форматы:*
• PDF (.pdf)
• Word документы (.docx, .doc)
• Текстовые файлы (.txt)

📤 *Как использовать:*
1. Отправьте файл резюме
2. Дождитесь обработки
3. Получите подтверждение

⚠️ *Ограничения:*
• Максимальный размер файла: {current_limit} MB
• Используется: {api_type}
• Для файлов >{STANDARD_BOT_API_LIMIT_MB} MB без Local Bot API используйте альтернативы

💡 *Команды:*
/start - Показать это сообщение
/upload_cv - Загрузить резюме
/help - Справка
/status - Статус сервиса
/conferences - ссылки на конференции
{admin_commands}
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_candidate_deep_link(update: Update, candidate_id: str) -> None:
    """Handle deep link to candidate profile"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен. Только для администраторов.")
        return
    
    # Show candidate profile
    await show_candidate_profile(update, candidate_id)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command - admin menu"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен. Только для администраторов.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📋 Списки", callback_data="admin_lists")],
        [InlineKeyboardButton("🔍 Поиск кандидата", callback_data="admin_search")],
        [InlineKeyboardButton("📊 Последние интервью", callback_data="admin_recent")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 *Админ меню*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def candidate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /candidate <id> command"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен. Только для администраторов.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Укажите ID кандидата: /candidate <id>")
        return
    
    candidate_id = context.args[0]
    await show_candidate_profile(update, candidate_id)

async def show_candidate_profile(update: Update, candidate_id: str) -> None:
    """Show candidate profile with inline buttons"""
    try:
        # Get candidate data from API
        response = requests.get(f"{MAIN_API_URL}/candidates/{candidate_id}", timeout=10)
        
        if response.status_code == 200:
            candidate_data = response.json()
            
            # Create inline keyboard
            keyboard = [
                [InlineKeyboardButton("📄 PDF отчёт", callback_data=f"report_pdf_{candidate_id}")],
                [InlineKeyboardButton("📊 Оценки по вопросам", callback_data=f"answers_{candidate_id}_1")],
                [InlineKeyboardButton("⏱️ Таймлиния Q/A", callback_data=f"timeline_{candidate_id}")],
                [
                    InlineKeyboardButton("✅ Pass", callback_data=f"decision_pass_{candidate_id}"),
                    InlineKeyboardButton("⏸️ Hold", callback_data=f"decision_hold_{candidate_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"decision_reject_{candidate_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            profile_text = f"""
👤 *Кандидат #{candidate_id}*

📧 Email: {candidate_data.get('email', 'Не указан')}
📱 Телефон: {candidate_data.get('phone', 'Не указан')}
📅 Дата подачи: {candidate_data.get('created_at', 'Не указана')}
📊 Статус: {candidate_data.get('status', 'Не указан')}

📈 *Оценки:*
{format_scores(candidate_data.get('scores', {}))}
"""
            
            await update.message.reply_text(
                profile_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(f"❌ Кандидат #{candidate_id} не найден")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении данных кандидата: {str(e)}")

def format_scores(scores: dict) -> str:
    """Format scores for display"""
    if not scores:
        return "Оценки не найдены"
    
    formatted = []
    for category, score in scores.items():
        formatted.append(f"• {category}: {score:.2f}")
    
    return "\n".join(formatted)


async def upload_cv_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /upload_cv command"""
    current_limit = LOCAL_BOT_API_LIMIT_MB if TELEGRAM_USE_LOCAL_BOT_API else STANDARD_BOT_API_LIMIT_MB
    api_type = "Local Bot API" if TELEGRAM_USE_LOCAL_BOT_API else "Standard Bot API"
    
    upload_message = f"""
📤 *Загрузка резюме*

Отправьте файл резюме в чат для обработки.

📋 *Поддерживаемые форматы:*
• PDF (.pdf) - рекомендуется
• Word (.docx, .doc)
• Текст (.txt)

📏 *Ограничения размера:*
• Текущий лимит: {current_limit} MB
• API: {api_type}

⚠️ *Важно:*
• Файлы >{STANDARD_BOT_API_LIMIT_MB} MB требуют Local Bot API
• Без Local Bot API используйте Pyrogram/Telethon
• Убедитесь, что PDF содержит текст, а не изображения

💡 *Альтернативы для больших файлов:*
• Local Bot API сервер
• MTProto клиенты (Telethon/Pyrogram)
• Веб-интерфейс AI-HR
    """
    
    await update.message.reply_text(
        upload_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    current_limit = LOCAL_BOT_API_LIMIT_MB if TELEGRAM_USE_LOCAL_BOT_API else STANDARD_BOT_API_LIMIT_MB
    
    help_message = f"""
📖 *Справка по использованию*

*Отправка резюме:*
Просто отправьте файл резюме в чат. Бот автоматически:
1. Проверит формат и размер
2. Скачает файл
3. Отправит на обработку в AI-HR систему
4. Уведомит о результате

*Поддерживаемые форматы:*
• PDF - наиболее предпочтительный
• DOCX/DOC - Word документы
• TXT - простой текст

*Ограничения размера:*
• Стандартный Bot API: до {STANDARD_BOT_API_LIMIT_MB} MB
• Local Bot API: до {LOCAL_BOT_API_LIMIT_MB} MB
• Текущий лимит: {current_limit} MB

*Альтернативы для больших файлов:*
• Local Bot API сервер (без лимитов)
• MTProto клиенты (Telethon/Pyrogram)
• Веб-интерфейс AI-HR

*Проблемы?*
Если файл не обрабатывается, проверьте:
• Формат файла
• Размер файла
• Качество PDF (не изображение)
• Доступность сервиса AI-HR
    """
    
    await update.message.reply_text(
        help_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - check CV service status"""
    try:
        response = requests.get(f"{CV_SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            status_message = f"""
✅ *Сервис AI-HR активен*

🔧 *Статус:*
• CV Service: {data.get('status', 'unknown')}
• Embedder: {data.get('embedder_model', 'unknown')}
• Qdrant: {data.get('qdrant_status', 'unknown')}
• Collection: {data.get('collection', 'unknown')}

📊 *Готов к обработке резюме*
            """
        else:
            status_message = "❌ *Сервис AI-HR недоступен*"
    except Exception as e:
        status_message = f"❌ *Ошибка подключения к сервису:*\n`{str(e)}`"
    
    await update.message.reply_text(
        status_message,
        parse_mode=ParseMode.MARKDOWN
    )

def is_supported_file(filename: str) -> bool:
    """Check if file extension is supported"""
    if not filename:
        return False
    
    file_ext = Path(filename).suffix.lower()
    return file_ext in SUPPORTED_EXTENSIONS

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle document uploads with Local Bot API support"""
    message: Message = update.message
    document = message.document
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
    
    # Determine current file size limit
    current_limit = LOCAL_BOT_API_LIMIT_MB if TELEGRAM_USE_LOCAL_BOT_API else STANDARD_BOT_API_LIMIT_MB
    max_size_bytes = current_limit * 1024 * 1024
    
    # Check file size
    if document.file_size > max_size_bytes:
        api_type = "Local Bot API" if TELEGRAM_USE_LOCAL_BOT_API else "Standard Bot API"
        
        # Special warning for files between 18-20 MB with standard API
        if not TELEGRAM_USE_LOCAL_BOT_API and document.file_size > 18 * 1024 * 1024:
            warning_message = f"""
⚠️ *Файл близок к лимиту*

Размер: {format_file_size(document.file_size)}
Лимит Standard Bot API: {STANDARD_BOT_API_LIMIT_MB} MB

💡 *Рекомендации:*
• Попробуйте сжать PDF
• Используйте Local Bot API сервер
• Альтернатива: MTProto клиенты (Telethon/Pyrogram)
• Веб-интерфейс AI-HR

🔧 *Настройка Local Bot API:*
TELEGRAM_USE_LOCAL_BOT_API=true
TELEGRAM_BOT_API_URL=http://localhost:8081

📋 *Альтернативные способы загрузки:*
• Публичная ссылка на файл
• MTProto-бот для больших файлов
• Веб-интерфейс AI-HR
            """
        else:
            warning_message = f"""
❌ *Файл слишком большой*

Размер: {format_file_size(document.file_size)}
Максимум ({api_type}): {current_limit} MB

💡 *Альтернативы:*
• Local Bot API сервер (до {LOCAL_BOT_API_LIMIT_MB} MB)
• MTProto клиенты (Telethon/Pyrogram)
• Веб-интерфейс AI-HR
• Публичная ссылка на файл

📋 *Для файлов >{current_limit}MB:*
• Настройте Local Bot API сервер
• Используйте MTProto-бот
• Загрузите через веб-интерфейс
            """
        
        await message.reply_text(
            warning_message,
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Check file extension
    if not is_supported_file(document.file_name):
        supported_list = ", ".join(SUPPORTED_EXTENSIONS)
        await message.reply_text(
            f"❌ *Неподдерживаемый формат файла*\n\n"
            f"Файл: `{document.file_name}`\n"
            f"Поддерживаемые: {supported_list}",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Send initial confirmation
    processing_message = await message.reply_text(
        f"📄 *Резюме получено*\n\n"
        f"Файл: `{document.file_name}`\n"
        f"Размер: {format_file_size(document.file_size)}\n\n"
        f"⏳ Обработка началась...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Show uploading indicator for large files
        if document.file_size > 10 * 1024 * 1024:  # > 10MB
            await context.bot.send_chat_action(chat_id=message.chat_id, action="upload_document")
        
        # Download file using appropriate API
        file = await context.bot.get_file(document.file_id)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            suffix=Path(document.file_name).suffix,
            delete=False
        ) as temp_file:
            temp_path = temp_file.name
        
        # Download to temporary file with progress indication
        await file.download_to_drive(temp_path)
        
        # Verify file was downloaded correctly
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            raise Exception("File download failed or file is empty")
        
        # Send to CV service
        with open(temp_path, 'rb') as f:
            files = {'file': (document.file_name, f, 'application/octet-stream')}
            response = requests.post(
                f"{CV_SERVICE_URL}/ingest",
                files=files,
                timeout=60
            )
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        # Handle response
        if response.status_code == 200:
            data = response.json()
            success_message = f"""
✅ *Резюме успешно обработано*

📋 *Детали:*
• CV ID: `{data['cv_id']}`
• Фрагментов: {data['chunks_created']}
• Длина текста: {data['total_text_length']} символов
• Время обработки: {data['processing_time']:.1f}с

🎯 *Готово к поиску и анализу*
            """
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_detail = error_data.get('detail', response.text)
            success_message = f"""
❌ *Ошибка обработки*

Детали: `{error_detail}`

Попробуйте:
• Проверить формат файла
• Убедиться, что файл не поврежден
• Отправить файл меньшего размера
            """
        
        await processing_message.edit_text(
            success_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except requests.exceptions.ConnectionError:
        await processing_message.edit_text(
            "❌ *Сервис AI-HR недоступен*\n\n"
            "Попробуйте позже или обратитесь к администратору",
            parse_mode=ParseMode.MARKDOWN
        )
    except requests.exceptions.Timeout:
        await processing_message.edit_text(
            "⏰ *Превышено время ожидания*\n\n"
            "Файл слишком большой или сервис перегружен",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await processing_message.edit_text(
            f"❌ *Неожиданная ошибка*\n\n"
            f"Детали: `{str(e)}`\n\n"
            f"Попробуйте отправить файл еще раз",
            parse_mode=ParseMode.MARKDOWN
        )
    finally:
        # Clean up temporary file if it still exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages"""
    await update.message.reply_text(
        "📄 Отправьте файл резюме для обработки\n\n"
        "Используйте /help для получения справки",
        parse_mode=ParseMode.MARKDOWN
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    print(f"Update {update} caused error {context.error}")

def main() -> None:
    """Start the bot"""
    current_limit = LOCAL_BOT_API_LIMIT_MB if TELEGRAM_USE_LOCAL_BOT_API else STANDARD_BOT_API_LIMIT_MB
    api_type = "Local Bot API" if TELEGRAM_USE_LOCAL_BOT_API else "Standard Bot API"
    
    print(f"Starting AI-HR Telegram Bot...")
    print(f"CV Service URL: {CV_SERVICE_URL}")
    print(f"Bot API Type: {api_type}")
    print(f"Max file size: {current_limit} MB")
    
    if TELEGRAM_USE_LOCAL_BOT_API:
        print(f"Local Bot API URL: {TELEGRAM_BOT_API_URL}")
    
    # Create application builder
    builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    
    # Configure local Bot API if enabled
    if TELEGRAM_USE_LOCAL_BOT_API:
        builder = builder.base_url(TELEGRAM_BOT_API_URL)
        print("Using Local Bot API server")
    
    # Build application
    application = builder.build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("upload_cv", upload_cv_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("candidate", candidate_command))
    
    # Add callback query handler for inline keyboards
    from handlers_admin import handle_callback_query
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add public command handlers
    from handlers_public import conferences_command, conf_add_command, conf_list_command, help_command, status_command
    application.add_handler(CommandHandler("conferences", conferences_command))
    application.add_handler(CommandHandler("conf_add", conf_add_command))
    application.add_handler(CommandHandler("conf_list", conf_list_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Add admin command handlers
    from handlers_admin import generate_links_command
    application.add_handler(CommandHandler("links", generate_links_command))
    
    # Add broadcast command handlers
    from handlers_broadcast import broadcast_command, broadcast_stats_command, add_user_command, handle_broadcast_callback
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("broadcast_stats", broadcast_stats_command))
    application.add_handler(CommandHandler("add_user", add_user_command))
    
    # Document handler (PDF, DOCX, etc.)
    application.add_handler(MessageHandler(
        filters.Document.ALL,
        handle_document
    ))
    
    # Text handler (fallback)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
