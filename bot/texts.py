from database.crud import PLAN_LIMITS, DAILY_LIMITS, PLAN_PRICES, PLAN_EMOJI, PLAN_STARS
from modes import AI_MODES

# ─────────────────────────────────────────────
#  AI descriptions
# ─────────────────────────────────────────────
AI_DESCRIPTIONS = {
    "chatgpt": {
        "name": "ChatGPT", "model": "GPT-4o", "emoji": "🟢",
        "tagline": "Универсальный помощник",
        "description": (
            "Мощная языковая модель от OpenAI. "
            "Отлично справляется с написанием текстов, кодом, анализом данных, "
            "переводами и общими вопросами."
        ),
    },
    "claude": {
        "name": "Claude", "model": "Sonnet 4.6", "emoji": "🟣",
        "tagline": "Аналитик и исследователь",
        "description": (
            "Флагманская модель Anthropic. Известна точностью рассуждений "
            "и способностью работать с большими объёмами текста."
        ),
    },
    "deepseek": {
        "name": "DeepSeek", "model": "V3", "emoji": "🔵",
        "tagline": "Скоростной и технический",
        "description": (
            "Передовая модель от DeepSeek. "
            "Специализируется на математике, логике и программировании."
        ),
    },
}


def get_welcome_text(first_name: str, is_new: bool = False) -> str:
    trial_block = (
        "\n🎁 <b>Бонус новичка:</b> 3 дня <b>Pro</b> бесплатно!\n"
        "Попробуй Claude и все возможности бота прямо сейчас.\n"
    ) if is_new else ""

    return (
        f"👋 Привет, <b>{first_name}</b>!\n\n"
        f"🤖 Добро пожаловать в <b>NEUR AI</b> — три лучших нейросети + генерация изображений.\n"
        f"{trial_block}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>ChatGPT</b> (GPT-4o) — универсальный\n"
        f"🟣 <b>Claude</b> (Sonnet 4.6) — аналитик\n"
        f"🔵 <b>DeepSeek</b> (V3) — технический\n"
        f"🎨 <b>DALL-E 3</b> — генерация изображений\n\n"
        f"🎙 Голосовые сообщения поддерживаются\n"
        f"💾 Сохраняй и загружай диалоги\n"
        f"🔄 Переключай нейросети прямо в чате\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>/menu — выбор ИИ · /plans — тарифы · /chats — история</i>"
    )


def get_ai_selection_text() -> str:
    lines = ["🤖 <b>Выбери нейросеть и режим работы</b>\n"]
    for key, info in AI_DESCRIPTIONS.items():
        lines.append(
            f"{info['emoji']} <b>{info['name']}</b> ({info['model']}) — {info['tagline']}"
        )
    lines.append("\n<i>После выбора модели выбери режим работы.</i>")
    lines.append("🎨 Для генерации изображений используй кнопку <b>«Картинка»</b>.")
    lines.append("\n👇 Нажми кнопку для выбора:")
    return "\n".join(lines)


def get_plans_text() -> str:
    text = "💳 <b>Тарифные планы NEUR AI</b>\n\n"
    plans_info = {
        "free":  {"name": "Бесплатный",  "price": "0",                        "features": ["🟢 ChatGPT: 5/мес · 3/день", "🔵 DeepSeek: 10/мес · 5/день", "🟣 Claude: недоступен", "🎨 Изображения: 1/день", "💾 Сохранение чатов: нет"]},
        "basic": {"name": "Basic",        "price": f"{PLAN_STARS['basic']} ⭐", "features": ["🟢 ChatGPT: 30/мес · 10/день", "🔵 DeepSeek: 50/мес · 20/день", "🟣 Claude: недоступен", "🎨 Изображения: 3/день", "💾 Сохранение чатов: 3"]},
        "pro":   {"name": "Pro",          "price": f"{PLAN_STARS['pro']} ⭐",   "features": ["🟢 ChatGPT: 80/мес · 30/день", "🟣 Claude: 10/мес · 5/день", "🔵 DeepSeek: 150/мес · 60/день", "🎨 Изображения: 10/день", "💾 Сохранение чатов: 20"]},
        "ultra": {"name": "Ultra",        "price": f"{PLAN_STARS['ultra']} ⭐", "features": ["🟢 ChatGPT: 200/мес · 80/день", "🟣 Claude: 30/мес · 15/день", "🔵 DeepSeek: ∞ безлимит", "🎨 Изображения: 30/день", "💾 Сохранение чатов: ∞"]},
    }
    for plan_key, plan in plans_info.items():
        emoji = PLAN_EMOJI.get(plan_key, "")
        text += f"{emoji} <b>{plan['name']}</b> — <b>{plan['price']}</b>\n"
        for f in plan["features"]:
            text += f"  {f}\n"
        text += "\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "⭐ Оплата через Telegram Stars — мгновенная активация!\n"
    text += "Нажми на тариф для деталей и оплаты."
    return text


def get_usage_text(sub, user=None) -> str:
    from services.image_service import IMAGE_DAILY_LIMITS
    plan = sub.plan
    lm = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    ld = DAILY_LIMITS.get(plan, DAILY_LIMITS["free"])
    img_limit = IMAGE_DAILY_LIMITS.get(plan, 0)
    emoji = PLAN_EMOJI.get(plan, "")

    def fmt(used, limit):
        return f"{used}/∞" if limit == -1 else ("—" if limit == 0 else f"{used}/{limit}")

    badge = ""
    if getattr(sub, "is_trial", False):
        badge = " · <b>🎁 Trial</b>"

    expires_str = ""
    if sub.expires_at:
        import datetime
        days_left = max(0, (sub.expires_at - datetime.datetime.utcnow()).days)
        expires_str = f"\n⏳ Осталось дней: <b>{days_left}</b>"

    img_used = getattr(sub, "daily_image_used", 0)
    img_str = f"—" if img_limit == 0 else f"{img_used}/{img_limit}"

    return (
        f"📊 <b>Ваш профиль</b>\n\n"
        f"{emoji} Тариф: <b>{plan.upper()}</b>{badge}{expires_str}\n\n"
        f"<b>Запросы (месяц / сегодня):</b>\n"
        f"🟢 ChatGPT:  {fmt(sub.chatgpt_used, lm['chatgpt'])} мес · {fmt(sub.daily_chatgpt_used, ld['chatgpt'])} день\n"
        f"🟣 Claude:   {fmt(sub.claude_used, lm['claude'])} мес · {fmt(sub.daily_claude_used, ld['claude'])} день\n"
        f"🔵 DeepSeek: {fmt(sub.deepseek_used, lm['deepseek'])} мес · {fmt(sub.daily_deepseek_used, ld['deepseek'])} день\n"
        f"🎨 Картинки: {img_str} день\n\n"
        f"🔄 Счётчики: месяц — раз в 30 дней, день — ежедневно"
    )
