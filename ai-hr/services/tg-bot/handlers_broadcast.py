# Обработчики рассылки Telegram бота
import os
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Set, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter, NetworkError

BROADCAST_DATA_FILE = Path(__file__).parent / "data" / "broadcast_data.json"
BROADCAST_THROTTLE_DELAY = 0.1
BROADCAST_MAX_RETRIES = 3
BROADCAST_RATE_LIMIT = 30
SEGMENTS = {
    "all": "Все пользователи",
    "ba": "Бизнес-аналитики",
    "it": "IT специалисты", 
    "dev": "Разработчики"
}

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    admins = os.getenv("TELEGRAM_ADMINS", "").split(",")
    admins = [int(admin.strip()) for admin in admins if admin.strip().isdigit()]
    return user_id in admins

def load_broadcast_data() -> Dict:
    """Load broadcast data from JSON file"""
    try:
        if BROADCAST_DATA_FILE.exists():
            with open(BROADCAST_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "users": {},  # user_id -> {segment, last_interview, created_at}
                "broadcasts": [],  # broadcast history
                "stats": {
                    "total_users": 0,
                    "segment_counts": {segment: 0 for segment in SEGMENTS.keys()}
                }
            }
    except Exception as e:
        print(f"Error loading broadcast data: {e}")
        return {"users": {}, "broadcasts": [], "stats": {"total_users": 0, "segment_counts": {}}}

def save_broadcast_data(data: Dict) -> bool:
    """Save broadcast data to JSON file"""
    try:
        BROADCAST_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BROADCAST_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving broadcast data: {e}")
        return False

def update_user_segment(user_id: int, segment: str, interview_data: Optional[Dict] = None) -> None:
    """Update user segment based on interview results"""
    data = load_broadcast_data()
    
    if user_id not in data["users"]:
        data["users"][str(user_id)] = {
            "segment": "all",
            "last_interview": None,
            "created_at": time.time(),
            "interview_count": 0
        }
    
    user_data = data["users"][str(user_id)]
    user_data["segment"] = segment
    user_data["last_interview"] = time.time()
    user_data["interview_count"] = user_data.get("interview_count", 0) + 1
    
    if interview_data:
        user_data["interview_data"] = interview_data
    
    # Update stats
    data["stats"]["total_users"] = len(data["users"])
    data["stats"]["segment_counts"] = {}
    for seg in SEGMENTS.keys():
        data["stats"]["segment_counts"][seg] = sum(
            1 for user in data["users"].values() 
            if user.get("segment") == seg
        )
    
    save_broadcast_data(data)

def auto_update_user_segment_from_interview(user_id: int, interview_results: Dict) -> None:
    """Automatically determine and update user segment based on interview results"""
    # Analyze interview results to determine segment
    scores = interview_results.get("scores", {})
    role_profile = interview_results.get("role_profile", "")
    
    # Determine segment based on role profile and scores
    if "ba" in role_profile.lower() or "anti" in role_profile.lower():
        segment = "ba"
    elif "it" in role_profile.lower() or "dc" in role_profile.lower():
        segment = "it"
    elif "dev" in role_profile.lower() or "development" in role_profile.lower():
        segment = "dev"
    else:
        # Default to 'all' if can't determine
        segment = "all"
    
    # Update user segment
    update_user_segment(user_id, segment, interview_results)

def get_users_by_segment(segment: str) -> List[int]:
    """Get list of user IDs for a specific segment"""
    data = load_broadcast_data()
    
    if segment == "all":
        return [int(user_id) for user_id in data["users"].keys()]
    else:
        return [
            int(user_id) for user_id, user_data in data["users"].items()
            if user_data.get("segment") == segment
        ]

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /broadcast command - send message to segment"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен. Только для администраторов.")
        return
    
    if not context.args:
        segments_text = "\n".join([f"• {seg}: {desc}" for seg, desc in SEGMENTS.items()])
        await update.message.reply_text(
            f"❌ Укажите сегмент: /broadcast <segment>\n\n"
            f"📋 *Доступные сегменты:*\n{segments_text}\n\n"
            f"Пример: /broadcast ba",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    segment = context.args[0].lower()
    
    if segment not in SEGMENTS:
        await update.message.reply_text(
            f"❌ Неизвестный сегмент: {segment}\n"
            f"Доступные: {', '.join(SEGMENTS.keys())}"
        )
        return
    
    # Get user count for segment
    users = get_users_by_segment(segment)
    user_count = len(users)
    
    if user_count == 0:
        await update.message.reply_text(
            f"❌ В сегменте '{SEGMENTS[segment]}' нет пользователей"
        )
        return
    
    # Create confirmation keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, отправить", callback_data=f"broadcast_confirm_{segment}"),
            InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    confirmation_message = f"""
📢 *Подтверждение рассылки*

🎯 *Сегмент:* {SEGMENTS[segment]}
👥 *Пользователей:* {user_count}
⏱️ *Время отправки:* ~{user_count * BROADCAST_THROTTLE_DELAY:.1f} секунд

⚠️ *Внимание:* Это отправит сообщение всем пользователям в сегменте.

Подтвердите отправку?
    """
    
    await update.message.reply_text(
        confirmation_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def handle_broadcast_callback(query, data: str) -> None:
    """Handle broadcast confirmation callbacks"""
    if data == "broadcast_cancel":
        await query.edit_message_text("❌ Рассылка отменена")
        return
    
    if data.startswith("broadcast_confirm_"):
        segment = data.replace("broadcast_confirm_", "")
        await execute_broadcast(query, segment)

async def execute_broadcast(query, segment: str) -> None:
    """Execute broadcast to segment"""
    try:
        users = get_users_by_segment(segment)
        user_count = len(users)
        
        if user_count == 0:
            await query.edit_message_text(f"❌ В сегменте '{SEGMENTS[segment]}' нет пользователей")
            return
        
        # Update message with progress
        await query.edit_message_text(
            f"📢 *Рассылка началась*\n\n"
            f"🎯 Сегмент: {SEGMENTS[segment]}\n"
            f"👥 Пользователей: {user_count}\n"
            f"⏳ Отправка... 0/{user_count}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Prepare broadcast message
        broadcast_message = f"""
🎉 *Новости AI-HR*

Привет! У нас есть обновления для сегмента "{SEGMENTS[segment]}":

📊 *Новые возможности:*
• Улучшенная обработка резюме
• Расширенная аналитика интервью
• Новые сценарии для {segment.upper()}

🔗 *Полезные ссылки:*
• [Веб-интерфейс](http://localhost:8080)
• [Конференции](/conferences)
• [Справка](/help)

💡 *Совет:* Регулярно обновляйте резюме для лучших результатов!

---
*Это автоматическое сообщение от AI-HR Bot*
        """
        
        # Send messages with throttling
        sent_count = 0
        failed_count = 0
        start_time = time.time()
        
        for i, user_id in enumerate(users):
            try:
                # Send message
                await query.bot.send_message(
                    chat_id=user_id,
                    text=broadcast_message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                sent_count += 1
                
                # Update progress every 10 messages
                if (i + 1) % 10 == 0 or i == len(users) - 1:
                    await query.edit_message_text(
                        f"📢 *Рассылка в процессе*\n\n"
                        f"🎯 Сегмент: {SEGMENTS[segment]}\n"
                        f"👥 Пользователей: {user_count}\n"
                        f"✅ Отправлено: {sent_count}\n"
                        f"❌ Ошибок: {failed_count}\n"
                        f"⏳ Прогресс: {i + 1}/{user_count}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                
                # Throttle to respect rate limits
                await asyncio.sleep(BROADCAST_THROTTLE_DELAY)
                
            except RetryAfter as e:
                # Handle rate limiting
                await asyncio.sleep(e.retry_after)
                try:
                    await query.bot.send_message(
                        chat_id=user_id,
                        text=broadcast_message,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                    sent_count += 1
                except:
                    failed_count += 1
                    
            except (TelegramError, NetworkError) as e:
                failed_count += 1
                print(f"Failed to send to user {user_id}: {e}")
                continue
        
        # Calculate final stats
        end_time = time.time()
        duration = end_time - start_time
        
        # Save broadcast record
        data = load_broadcast_data()
        broadcast_record = {
            "segment": segment,
            "user_count": user_count,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "duration": duration,
            "timestamp": time.time(),
            "admin_id": query.from_user.id
        }
        data["broadcasts"].append(broadcast_record)
        save_broadcast_data(data)
        
        # Final report
        success_rate = (sent_count / user_count * 100) if user_count > 0 else 0
        
        final_message = f"""
✅ *Рассылка завершена*

🎯 *Сегмент:* {SEGMENTS[segment]}
👥 *Всего пользователей:* {user_count}
✅ *Отправлено:* {sent_count}
❌ *Ошибок:* {failed_count}
📊 *Успешность:* {success_rate:.1f}%
⏱️ *Время:* {duration:.1f} секунд

📈 *Статистика:*
• Скорость: {sent_count/duration:.1f} сообщений/сек
• Среднее время на сообщение: {duration/sent_count:.2f} сек
        """
        
        await query.edit_message_text(
            final_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка рассылки: {str(e)}")

async def broadcast_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show broadcast statistics (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен. Только для администраторов.")
        return
    
    data = load_broadcast_data()
    stats = data.get("stats", {})
    broadcasts = data.get("broadcasts", [])
    
    # Calculate recent broadcast stats
    recent_broadcasts = [b for b in broadcasts if time.time() - b.get("timestamp", 0) < 86400]  # Last 24h
    
    stats_message = f"""
📊 *Статистика рассылок*

👥 *Пользователи:*
• Всего: {stats.get('total_users', 0)}
"""
    
    for segment, count in stats.get("segment_counts", {}).items():
        stats_message += f"• {SEGMENTS.get(segment, segment)}: {count}\n"
    
    stats_message += f"""
📢 *Рассылки (24ч):*
• Отправлено: {len(recent_broadcasts)}
• Всего сообщений: {sum(b.get('sent_count', 0) for b in recent_broadcasts)}
• Успешность: {sum(b.get('sent_count', 0) for b in recent_broadcasts) / max(sum(b.get('user_count', 0) for b in recent_broadcasts), 1) * 100:.1f}%

📈 *Последние рассылки:*
"""
    
    for broadcast in recent_broadcasts[-5:]:  # Last 5 broadcasts
        segment_name = SEGMENTS.get(broadcast.get("segment", ""), broadcast.get("segment", ""))
        timestamp = time.strftime("%H:%M", time.localtime(broadcast.get("timestamp", 0)))
        stats_message += f"• {segment_name}: {broadcast.get('sent_count', 0)}/{broadcast.get('user_count', 0)} ({timestamp})\n"
    
    await update.message.reply_text(
        stats_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add user to broadcast system (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен. Только для администраторов.")
        return
    
    if not context.args or len(context.args) < 2:
        segments_text = "\n".join([f"• {seg}: {desc}" for seg, desc in SEGMENTS.items()])
        await update.message.reply_text(
            f"❌ Укажите пользователя и сегмент: /add_user <user_id> <segment>\n\n"
            f"📋 *Доступные сегменты:*\n{segments_text}\n\n"
            f"Пример: /add_user 123456789 ba",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        segment = context.args[1].lower()
        
        if segment not in SEGMENTS:
            await update.message.reply_text(
                f"❌ Неизвестный сегмент: {segment}\n"
                f"Доступные: {', '.join(SEGMENTS.keys())}"
            )
            return
        
        # Add user to segment
        update_user_segment(target_user_id, segment)
        
        await update.message.reply_text(
            f"✅ Пользователь {target_user_id} добавлен в сегмент '{SEGMENTS[segment]}'"
        )
        
    except ValueError:
        await update.message.reply_text("❌ Неверный ID пользователя. Используйте числовой ID.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
