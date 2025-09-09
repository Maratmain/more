# Публичные обработчики Telegram бота
import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

MAIN_API_URL = os.getenv("MAIN_API_URL", "http://api:8001")
CONFERENCES_FILE = Path(__file__).parent / "data" / "conferences.json"

def is_admin(user_id: int) -> bool:
    admins = os.getenv("TELEGRAM_ADMINS", "").split(",")
    admins = [int(admin.strip()) for admin in admins if admin.strip().isdigit()]
    return user_id in admins

def load_conferences() -> Dict[str, Any]:
    """Load conferences from JSON file"""
    try:
        with open(CONFERENCES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading conferences: {e}")
        return {}

def save_conferences(conferences: Dict[str, Any]) -> bool:
    """Save conferences to JSON file"""
    try:
        with open(CONFERENCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(conferences, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving conferences: {e}")
        return False

async def conferences_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /conferences command - show conference categories"""
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    
    conferences = load_conferences()
    
    if not conferences:
        await update.message.reply_text("❌ Список конференций временно недоступен")
        return
    
    keyboard = []
    fallback_text = "🎪 *Выберите категорию конференции:*\n\n"
    
    for category, data in conferences.items():
        title = data.get("title", category)
        keyboard.append([InlineKeyboardButton(
            title, 
            callback_data=f"conf_{category}"
        )])
        fallback_text += f"• {title}\n"
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Add fallback text for clients without buttons
    fallback_text += "\n💡 *Альтернатива:* Если кнопки не отображаются, используйте команды напрямую"
    
    await update.message.reply_text(
        fallback_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def conf_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /conf_add command - add conference (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен. Только для администраторов.")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Неверный формат команды.\n"
            "Использование: /conf_add <категория> <url> [название]\n"
            "Пример: /conf_add Data/AI https://example.com AI Conference"
        )
        return
    
    category = context.args[0]
    url = context.args[1]
    name = context.args[2] if len(context.args) > 2 else "Новая конференция"
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ URL должен начинаться с http:// или https://")
        return
    
    # Load current conferences
    conferences = load_conferences()
    
    # Add conference to category
    if category not in conferences:
        conferences[category] = {
            "title": f"📋 {category}",
            "description": f"Конференции по {category}",
            "links": []
        }
    
    # Add new conference
    new_conference = {
        "name": name,
        "url": url,
        "description": f"Добавлено администратором {user_id}"
    }
    
    conferences[category]["links"].append(new_conference)
    
    # Save conferences
    if save_conferences(conferences):
        await update.message.reply_text(
            f"✅ Конференция добавлена!\n"
            f"📋 Категория: {category}\n"
            f"🔗 Название: {name}\n"
            f"🌐 URL: {url}"
        )
    else:
        await update.message.reply_text("❌ Ошибка при сохранении конференции")

async def conf_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /conf_list command - list all conferences (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен. Только для администраторов.")
        return
    
    conferences = load_conferences()
    
    if not conferences:
        await update.message.reply_text("📋 Список конференций пуст")
        return
    
    message = "📋 *Все конференции:*\n\n"
    
    for category, data in conferences.items():
        message += f"**{data.get('title', category)}**\n"
        message += f"{data.get('description', '')}\n"
        
        links = data.get('links', [])
        for i, link in enumerate(links[:3], 1):  # Show first 3
            message += f"{i}. [{link.get('name', 'Без названия')}]({link.get('url', '#')})\n"
        
        if len(links) > 3:
            message += f"... и еще {len(links) - 3} конференций\n"
        
        message += "\n"
    
    await update.message.reply_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

async def handle_conference_callback(query, data: str) -> None:
    """Handle conference category selection"""
    category = data.replace("conf_", "")
    conferences = load_conferences()
    
    if category not in conferences:
        await query.edit_message_text(f"❌ Категория {category} не найдена")
        return
    
    category_data = conferences[category]
    links = category_data.get("links", [])
    
    if not links:
        await query.edit_message_text(f"📋 В категории {category} пока нет конференций")
        return
    
    # Create message with conference links
    message = f"{category_data.get('title', category)}\n\n"
    message += f"{category_data.get('description', '')}\n\n"
    
    # Add conference links
    for i, link in enumerate(links, 1):
        message += f"{i}. [{link.get('name', 'Без названия')}]({link.get('url', '#')})\n"
        if link.get('description'):
            message += f"   _{link['description']}_\n"
        message += "\n"
    
    # Create keyboard with URL buttons for first few conferences
    keyboard = []
    for i, link in enumerate(links[:5], 1):  # Show buttons for first 5
        keyboard.append([InlineKeyboardButton(
            f"🔗 {link.get('name', f'Конференция {i}')}",
            url=link.get('url', '#')
        )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data="conf_back")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def handle_conf_back(query) -> None:
    """Handle back to conference categories"""
    conferences = load_conferences()
    
    keyboard = []
    for category, data in conferences.items():
        keyboard.append([InlineKeyboardButton(
            data.get("title", category), 
            callback_data=f"conf_{category}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎪 *Выберите категорию конференции:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    user_id = update.effective_user.id
    is_admin_user = is_admin(user_id)
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    
    help_text = """
🤖 *AI-HR Bot - Справка*

*Основные команды:*
/start - Начать работу с ботом
/upload_cv - Загрузить резюме
/conferences - Список конференций
/help - Эта справка
/status - Статус сервисов

*Для загрузки резюме:*
1. Отправьте файл (PDF, DOCX, DOC, TXT)
2. Дождитесь обработки
3. Получите подтверждение

*Ограничения файлов:*
• Стандартный Bot API: до 20MB
• Local Bot API: до 2GB
• Поддерживаемые форматы: PDF, DOCX, DOC, TXT

*Альтернативы для больших файлов:*
• Публичная ссылка на файл
• MTProto-бот для файлов >20MB
• Веб-интерфейс AI-HR
"""
    
    if is_admin_user:
        help_text += """
*Админ команды:*
/admin - Админ меню
/candidate <id> - Профиль кандидата
/links <id> - Deep links для кандидата
/conf_add <категория> <url> [название] - Добавить конференцию
/conf_list - Список всех конференций
/broadcast <сегмент> - Рассылка по сегментам
/broadcast_stats - Статистика рассылок
/add_user <user_id> <сегмент> - Добавить пользователя

*Сегменты для рассылки:*
• all - Все пользователи
• ba - Бизнес-аналитики
• it - IT специалисты
• dev - Разработчики
"""
    
    # Add fallback text for clients without buttons
    help_text += """
*Альтернативный доступ:*
Если кнопки не отображаются, используйте команды напрямую:
• /start - начать работу
• /upload_cv - загрузить резюме
• /conferences - список конференций
• /help - эта справка
• /status - статус сервисов
"""
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command"""
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.message.chat_id, action="typing")
    
    status_text = "🔍 *Статус сервисов AI-HR:*\n\n"
    
    # Check main API
    try:
        response = requests.get(f"{MAIN_API_URL}/health", timeout=5)
        if response.status_code == 200:
            status_text += "✅ Main API: Работает\n"
        else:
            status_text += "⚠️ Main API: Проблемы\n"
    except:
        status_text += "❌ Main API: Недоступен\n"
    
    # Check CV service
    try:
        cv_url = os.getenv("CV_SERVICE_URL", "http://cv:8007")
        response = requests.get(f"{cv_url}/health", timeout=5)
        if response.status_code == 200:
            status_text += "✅ CV Service: Работает\n"
        else:
            status_text += "⚠️ CV Service: Проблемы\n"
    except:
        status_text += "❌ CV Service: Недоступен\n"
    
    # Check Report service
    try:
        report_url = os.getenv("REPORT_API_URL", "http://report:8005")
        response = requests.get(f"{report_url}/health", timeout=5)
        if response.status_code == 200:
            status_text += "✅ Report Service: Работает\n"
        else:
            status_text += "⚠️ Report Service: Проблемы\n"
    except:
        status_text += "❌ Report Service: Недоступен\n"
    
    # Bot configuration
    status_text += f"\n📋 *Конфигурация бота:*\n"
    status_text += f"• Local Bot API: {'Включен' if os.getenv('TELEGRAM_USE_LOCAL_BOT_API', 'false').lower() == 'true' else 'Отключен'}\n"
    status_text += f"• Админов: {len(os.getenv('TELEGRAM_ADMINS', '').split(',')) if os.getenv('TELEGRAM_ADMINS') else 0}\n"
    
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
