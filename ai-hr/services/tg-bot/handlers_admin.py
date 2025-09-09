# Админ-обработчики Telegram бота
import os
import tempfile
import requests
from typing import Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

REPORT_API_URL = os.getenv("REPORT_API_URL", "http://report:8005")
MAIN_API_URL = os.getenv("MAIN_API_URL", "http://api:8001")
CV_SERVICE_URL = os.getenv("CV_SERVICE_URL", "http://cv:8007")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    # Check admin permissions for admin functions
    if data.startswith(("admin_", "report_", "scores_", "timeline_", "decision_")):
        if not is_admin(user_id):
            await query.edit_message_text("❌ Доступ запрещен. Только для администраторов.")
            return
    
    # Route to appropriate handler
    if data.startswith("admin_"):
        await handle_admin_callback(query, data)
    elif data.startswith("report_pdf_"):
        candidate_id = data.replace("report_pdf_", "")
        await on_report_pdf(query, candidate_id)
    elif data.startswith("scores_"):
        candidate_id = data.replace("scores_", "")
        await on_scores_view(query, candidate_id)
    elif data.startswith("timeline_"):
        candidate_id = data.replace("timeline_", "")
        await on_timeline_view(query, candidate_id)
    elif data.startswith("answers_"):
        # Handle answers pagination: answers_sessionid_page
        parts = data.split("_")
        if len(parts) >= 3:
            session_id = parts[1]
            page = int(parts[2])
            await on_answers_page(query, session_id, page)
    elif data.startswith("decision_"):
        parts = data.split("_")
        decision = parts[1]  # pass, hold, reject
        candidate_id = parts[2]
        await on_decision_make(query, decision, candidate_id)
    elif data.startswith("conf_"):
        if data == "conf_back":
            from handlers_public import handle_conf_back
            await handle_conf_back(query)
        else:
            from handlers_public import handle_conference_callback
            await handle_conference_callback(query, data)
    elif data.startswith("broadcast_"):
        from handlers_broadcast import handle_broadcast_callback
        await handle_broadcast_callback(query, data)
    elif data == "noop":
        # No operation - just acknowledge
        await query.answer()

def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    admins = os.getenv("TELEGRAM_ADMINS", "").split(",")
    admins = [int(admin.strip()) for admin in admins if admin.strip().isdigit()]
    return user_id in admins

def generate_deep_links(candidate_id: str) -> Dict[str, str]:
    """Генерация deep links для кандидата и отчёта"""
    bot_username = os.getenv("BOT_USERNAME", "ai_hr_bot")
    
    return {
        "candidate": f"https://t.me/{bot_username}?start=cand_{candidate_id}",
        "report": f"https://t.me/{bot_username}?start=report_{candidate_id}",
        "mini_app": f"https://t.me/{bot_username}?start=cand_{candidate_id}"
    }

async def handle_admin_callback(query, data: str) -> None:
    """Handle admin menu callbacks"""
    if data == "admin_lists":
        await show_candidate_lists(query)
    elif data == "admin_search":
        await show_search_menu(query)
    elif data == "admin_recent":
        await show_recent_interviews(query)

async def show_candidate_lists(query) -> None:
    """Show candidate lists"""
    try:
        # Get recent candidates from CV service
        response = requests.get(f"{CV_SERVICE_URL}/cvs/list", timeout=10)
        
        if response.status_code == 200:
            candidates = response.json().get("cvs", [])
            
            if candidates:
                # Show first 10 candidates
                candidates_text = "📋 *Последние кандидаты:*\n\n"
                for i, cv_id in enumerate(candidates[:10], 1):
                    candidates_text += f"{i}. `{cv_id}`\n"
                
                # Create inline keyboard for each candidate
                keyboard = []
                for cv_id in candidates[:5]:  # Show buttons for first 5
                    keyboard.append([InlineKeyboardButton(f"👤 {cv_id}", callback_data=f"candidate_{cv_id}")])
                
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                
                await query.edit_message_text(
                    candidates_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text("📋 Список кандидатов пуст")
        else:
            await query.edit_message_text("❌ Ошибка при получении списка кандидатов")
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def show_search_menu(query) -> None:
    """Show search menu"""
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск по навыкам", callback_data="search_skills")],
        [InlineKeyboardButton("📧 Поиск по email", callback_data="search_email")],
        [InlineKeyboardButton("📅 Поиск по дате", callback_data="search_date")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔍 *Поиск кандидатов*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def show_recent_interviews(query) -> None:
    """Show recent interviews"""
    try:
        # Get recent interviews from main API
        response = requests.get(f"{MAIN_API_URL}/interviews/recent", timeout=10)
        
        if response.status_code == 200:
            interviews = response.json().get("interviews", [])
            
            if interviews:
                interviews_text = "📊 *Последние интервью:*\n\n"
                for interview in interviews[:10]:
                    interviews_text += f"• {interview.get('candidate_id', 'N/A')} - {interview.get('status', 'N/A')}\n"
                
                await query.edit_message_text(interviews_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text("📊 Нет недавних интервью")
        else:
            await query.edit_message_text("❌ Ошибка при получении интервью")
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def on_report_pdf(query, candidate_id: str) -> None:
    """Generate and send PDF report for candidate"""
    try:
        await query.edit_message_text("📄 Генерирую PDF отчёт...")
        
        # Get candidate data
        candidate_response = requests.get(f"{MAIN_API_URL}/candidates/{candidate_id}", timeout=10)
        
        if candidate_response.status_code != 200:
            await query.edit_message_text(f"❌ Кандидат #{candidate_id} не найден")
            return
        
        candidate_data = candidate_response.json()
        
        # Prepare report request
        report_request = {
            "candidate_id": candidate_id,
            "candidate_data": candidate_data,
            "blocks": candidate_data.get("scores", {}),
            "evaluation": {
                "overall_score": sum(candidate_data.get("scores", {}).values()) / len(candidate_data.get("scores", {})) if candidate_data.get("scores") else 0,
                "recommendation": "Pass" if sum(candidate_data.get("scores", {}).values()) / len(candidate_data.get("scores", {})) > 0.7 else "Hold"
            }
        }
        
        # Generate PDF report
        report_response = requests.post(
            f"{REPORT_API_URL}/report/render",
            json=report_request,
            timeout=30
        )
        
        if report_response.status_code == 200:
            # Save PDF to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(report_response.content)
                temp_file_path = temp_file.name
            
            # Send PDF document
            with open(temp_file_path, 'rb') as pdf_file:
                await query.message.reply_document(
                    document=pdf_file,
                    filename=f"report_{candidate_id}.pdf",
                    caption=f"📄 Отчёт по кандидату #{candidate_id}"
                )
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Generate deep links for quick access
            bot_username = os.getenv("BOT_USERNAME", "ai_hr_bot")
            candidate_deep_link = f"https://t.me/{bot_username}?start=cand_{candidate_id}"
            report_deep_link = f"https://t.me/{bot_username}?start=report_{candidate_id}"
            
            await query.edit_message_text(
                f"✅ PDF отчёт для кандидата #{candidate_id} отправлен\n\n"
                f"🔗 *Быстрые ссылки:*\n"
                f"• [Профиль кандидата]({candidate_deep_link})\n"
                f"• [Отчёт]({report_deep_link})\n\n"
                f"💡 *Использование:*\n"
                f"• Скопируйте ссылку для быстрого доступа\n"
                f"• В мобильном клиенте откроется сразу\n"
                f"• В десктопе может появиться кнопка START",
                parse_mode=ParseMode.MARKDOWN
            )
            
        else:
            # Fallback: send web link
            web_url = f"{REPORT_API_URL}/report/web/{candidate_id}"
            await query.edit_message_text(
                f"❌ Ошибка генерации PDF. Веб-версия: {web_url}",
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка при генерации отчёта: {str(e)}")

async def on_scores_view(query, candidate_id: str) -> None:
    """Show detailed scores for candidate"""
    try:
        # Get candidate data
        response = requests.get(f"{MAIN_API_URL}/candidates/{candidate_id}", timeout=10)
        
        if response.status_code == 200:
            candidate_data = response.json()
            scores = candidate_data.get("scores", {})
            
            if scores:
                scores_text = f"📊 *Оценки кандидата #{candidate_id}:*\n\n"
                for category, score in scores.items():
                    score_bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                    scores_text += f"• {category}: {score:.2f}\n{score_bar}\n\n"
                
                await query.edit_message_text(scores_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text(f"📊 Оценки для кандидата #{candidate_id} не найдены")
        else:
            await query.edit_message_text(f"❌ Кандидат #{candidate_id} не найден")
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def on_timeline_view(query, candidate_id: str) -> None:
    """Show Q/A timeline for candidate"""
    try:
        # Get interview timeline
        response = requests.get(f"{MAIN_API_URL}/interviews/{candidate_id}/timeline", timeout=10)
        
        if response.status_code == 200:
            timeline_data = response.json()
            
            if timeline_data.get("timeline"):
                timeline_text = f"⏱️ *Таймлиния Q/A для кандидата #{candidate_id}:*\n\n"
                
                for i, item in enumerate(timeline_data["timeline"][:10], 1):
                    timeline_text += f"{i}. **Q:** {item.get('question', 'N/A')}\n"
                    timeline_text += f"   **A:** {item.get('answer', 'N/A')}\n"
                    timeline_text += f"   **Score:** {item.get('score', 'N/A')}\n\n"
                
                await query.edit_message_text(timeline_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text(f"⏱️ Таймлиния для кандидата #{candidate_id} не найдена")
        else:
            await query.edit_message_text(f"❌ Таймлиния для кандидата #{candidate_id} не найдена")
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def on_answers_page(query, session_id: str, page: int = 1) -> None:
    """Show paginated interview answers"""
    try:
        # Get interview answers from API
        response = requests.get(f"{MAIN_API_URL}/interview/{session_id}/answers?page={page}&page_size=5", timeout=10)
        
        if response.status_code == 200:
            answers_data = response.json()
            answers = answers_data.get("answers", [])
            total_answers = answers_data.get("total_answers", 0)
            current_page = answers_data.get("page", 1)
            page_size = answers_data.get("page_size", 5)
            rating = answers_data.get("rating_0_10", 0.0)
            
            if answers:
                # Format answers message
                answers_text = f"📊 *Оценки по вопросам (сессия {session_id})*\n"
                answers_text += f"📈 Общий рейтинг: {rating:.1f}/10\n"
                answers_text += f"📄 Страница {current_page} из {(total_answers + page_size - 1) // page_size}\n\n"
                
                for answer in answers:
                    # Format score bar
                    score_bar = "█" * int(answer["score"] * 10) + "░" * (10 - int(answer["score"] * 10))
                    
                    # Format red flags
                    flags_text = ""
                    if answer.get("red_flags"):
                        flags_text = f"🚩 {', '.join(answer['red_flags'])}"
                    
                    # Format question quote (first 50 chars)
                    question_quote = answer["question_text"][:50] + "..." if len(answer["question_text"]) > 50 else answer["question_text"]
                    
                    answers_text += f"**Q{answer['order']}** | {answer['block']} | L{answer['order']} | {answer['weight']:.1f} | {answer['score']:.2f} | {flags_text}\n"
                    answers_text += f"{score_bar} | \"{question_quote}\"\n\n"
                
                # Create pagination keyboard
                keyboard = []
                
                # Pagination buttons
                nav_buttons = []
                if current_page > 1:
                    nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"answers_{session_id}_{current_page-1}"))
                
                nav_buttons.append(InlineKeyboardButton(f"{current_page}", callback_data="noop"))
                
                if current_page * page_size < total_answers:
                    nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"answers_{session_id}_{current_page+1}"))
                
                if nav_buttons:
                    keyboard.append(nav_buttons)
                
                # Timeline button (URL to mini-app)
                mini_app_url = f"https://t.me/your_bot?start=cand_{session_id}"
                keyboard.append([InlineKeyboardButton("⏱️ Таймлиния Q/A", url=mini_app_url)])
                
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                
                await query.edit_message_text(
                    answers_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(f"📊 Нет ответов для сессии {session_id}")
        else:
            await query.edit_message_text(f"❌ Ошибка при получении ответов для сессии {session_id}")
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def on_decision_make(query, decision: str, candidate_id: str) -> None:
    """Make decision for candidate (Pass/Hold/Reject)"""
    try:
        # Update candidate decision
        decision_data = {
            "candidate_id": candidate_id,
            "decision": decision,
            "updated_by": query.from_user.id,
            "notes": f"Решение принято через Telegram Bot"
        }
        
        response = requests.post(
            f"{MAIN_API_URL}/candidates/{candidate_id}/decision",
            json=decision_data,
            timeout=10
        )
        
        if response.status_code == 200:
            decision_emoji = {"pass": "✅", "hold": "⏸️", "reject": "❌"}
            decision_text = {"pass": "Pass", "hold": "Hold", "reject": "Reject"}
            
            await query.edit_message_text(
                f"{decision_emoji.get(decision, '📝')} Решение для кандидата #{candidate_id}: **{decision_text.get(decision, decision)}**",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text(f"❌ Ошибка при сохранении решения")
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def generate_links_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate deep links for candidate (admin only)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Доступ запрещен. Только для администраторов.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID кандидата: /links <candidate_id>\n"
            "Пример: /links test_123"
        )
        return
    
    candidate_id = context.args[0]
    deep_links = generate_deep_links(candidate_id)
    
    links_message = f"""
🔗 *Deep Links для кандидата #{candidate_id}*

📱 *Профиль кандидата:*
`{deep_links['candidate']}`

📄 *PDF отчёт:*
`{deep_links['report']}`

🌐 *Mini-App:*
`{deep_links['mini_app']}`

💡 *Использование:*
• Скопируйте ссылку для быстрого доступа
• В мобильном клиенте откроется сразу
• В десктопе может появиться кнопка START
• Можно использовать в других приложениях

📋 *Альтернатива:*
Если deep links не работают, используйте веб-интерфейс:
http://localhost:8080/candidate.html?id={candidate_id}
    """
    
    await update.message.reply_text(
        links_message,
        parse_mode=ParseMode.MARKDOWN
    )

