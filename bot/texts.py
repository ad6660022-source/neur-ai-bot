from database.crud import PLAN_LIMITS, DAILY_LIMITS, PLAN_PRICES, PLAN_EMOJI, PLAN_STARS

# ─────────────────────────────────────────────
#  AI descriptions
# ─────────────────────────────────────────────
AI_DESCRIPTIONS = {
    "chatgpt": {
        "name": "ChatGPT",
        "model": "GPT-4o",
        "emoji": "🟢",
        "tagline": "Универсальный помощник",
        "description": (
            "Мощная языковая модель от OpenAI. "
            "Отлично справляется с написанием текстов, кодом, анализом данных, "
            "переводами и общими вопросами. Поддерживает длинный контекст диалога."
        ),
        "best_for": [
            "✍️ Написание текстов и эссе",
            "💻 Программирование и отладка кода",
            "📊 Анализ и структурирование данных",
            "🌍 Переводы и редактирование",
            "🧠 Брейнсторминг и генерация идей",
        ],
    },
    "claude": {
        "name": "Claude",
        "model": "Claude Sonnet 4.6",
        "emoji": "🟣",
        "tagline": "Аналитик и исследователь",
        "description": (
            "Флагманская модель Anthropic. Известна точностью рассуждений, "
            "честностью ответов и способностью работать с большими объёмами текста. "
            "Идеальна для сложного анализа и научных задач."
        ),
        "best_for": [
            "📚 Работа с большими документами",
            "🔬 Научный и юридический анализ",
            "📝 Детальные исследования и рефераты",
            "🎯 Точные и взвешенные ответы",
            "🏗️ Сложные технические задачи",
        ],
    },
    "deepseek": {
        "name": "DeepSeek",
        "model": "DeepSeek-V3",
        "emoji": "🔵",
        "tagline": "Скоростной и технический",
        "description": (
            "Передовая модель от DeepSeek. "
            "Специализируется на математике, логике и программировании. "
            "Работает быстро и даёт детальные технические объяснения."
        ),
        "best_for": [
            "🧮 Математика и алгоритмы",
            "💡 Логические задачи и головоломки",
            "⚡ Быстрые технические вопросы",
            "🛠️ Системное программирование",
            "📐 Формулы, расчёты, схемы",
        ],
    },
}


def get_welcome_text(first_name: str) -> str:
    return (
        f"👋 Привет, <b>{first_name}</b>!\n\n"
        f"🤖 Добро пожаловать в <b>NEUR AI</b> — твой личный доступ к\n"
        f"трём лучшим нейросетям в одном боте.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Доступные нейросети:</b>\n\n"
        f"🟢 <b>ChatGPT</b> (GPT-4o) — универсальный помощник\n"
        f"🟣 <b>Claude</b> (Sonnet 4.6) — аналитик и исследователь\n"
        f"🔵 <b>DeepSeek</b> (V3) — технический и математический\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 На старте тебе доступны <b>бесплатные запросы</b>.\n"
        f"Выбери нейросеть и начни общение!\n\n"
        f"💡 <i>/menu — выбор ИИ · /plans — тарифы</i>"
    )


def get_ai_selection_text() -> str:
    lines = ["🤖 <b>Выбери нейросеть для работы</b>\n"]
    for key, info in AI_DESCRIPTIONS.items():
        lines.append(f"{info['emoji']} <b>{info['name']}</b> ({info['model']}) — {info['tagline']}")
    lines.append("\n👇 Нажми кнопку для выбора:")
    return "\n".join(lines)


def get_plans_text() -> str:
    text = "💳 <b>Тарифные планы NEUR AI</b>\n\n"

    plans_info = {
        "free": {
            "name": "Бесплатный",
            "price_label": "0 ₽ / мес",
            "stars_label": None,
            "features": [
                "🟢 ChatGPT: 5/мес · 3/день",
                "🔵 DeepSeek: 10/мес · 5/день",
                "🟣 Claude: недоступен",
            ],
        },
        "basic": {
            "name": "Basic",
            "price_label": "~450 ₽ / мес",
            "stars_label": f"{PLAN_STARS['basic']} ⭐",
            "features": [
                "🟢 ChatGPT: 30/мес · 10/день",
                "🔵 DeepSeek: 50/мес · 20/день",
                "🟣 Claude: недоступен",
            ],
        },
        "pro": {
            "name": "Pro",
            "price_label": "~900 ₽ / мес",
            "stars_label": f"{PLAN_STARS['pro']} ⭐",
            "features": [
                "🟢 ChatGPT: 80/мес · 30/день",
                "🟣 Claude: 10/мес · 5/день",
                "🔵 DeepSeek: 150/мес · 60/день",
            ],
        },
        "ultra": {
            "name": "Ultra",
            "price_label": "~1800 ₽ / мес",
            "stars_label": f"{PLAN_STARS['ultra']} ⭐",
            "features": [
                "🟢 ChatGPT: 200/мес · 80/день",
                "🟣 Claude: 30/мес · 15/день",
                "🔵 DeepSeek: ∞ безлимит",
            ],
        },
    }

    for plan_key, plan in plans_info.items():
        emoji = PLAN_EMOJI.get(plan_key, "")
        price = plan["price_label"]
        stars = f" | {plan['stars_label']}" if plan["stars_label"] else ""
        text += f"{emoji} <b>{plan['name']}</b> — <b>{price}{stars}</b>\n"
        for feature in plan["features"]:
            text += f"  {feature}\n"
        text += "\n"

    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "⭐ <b>Оплата через Telegram Stars</b> — мгновенная активация!\n"
    text += "Нажми на тариф чтобы перейти к оплате."
    return text


def get_usage_text(sub, user=None) -> str:
    plan = sub.plan
    limits_m = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    limits_d = DAILY_LIMITS.get(plan, DAILY_LIMITS["free"])
    emoji = PLAN_EMOJI.get(plan, "")

    def fmt_m(used, limit):
        if limit == -1:
            return f"{used}/∞"
        return f"{used}/{limit}"

    def fmt_d(used, limit):
        if limit == -1:
            return "∞"
        if limit == 0:
            return "—"
        return f"{used}/{limit}"

    expires_str = ""
    if sub.expires_at:
        days_left = (sub.expires_at - __import__("datetime").datetime.utcnow()).days
        expires_str = f"\n⏳ Осталось дней: <b>{max(0, days_left)}</b>"

    bonus_str = ""
    if user and user.bonus_requests > 0:
        bonus_str = f"\n🎁 Бонусных запросов: <b>{user.bonus_requests}</b>"

    text = (
        f"📊 <b>Ваш профиль</b>\n\n"
        f"{emoji} Тариф: <b>{plan.upper()}</b>{expires_str}{bonus_str}\n\n"
        f"<b>Запросы (месяц / сегодня):</b>\n"
        f"🟢 ChatGPT:  {fmt_m(sub.chatgpt_used, limits_m['chatgpt'])} мес · {fmt_d(sub.daily_chatgpt_used, limits_d['chatgpt'])} день\n"
        f"🟣 Claude:   {fmt_m(sub.claude_used, limits_m['claude'])} мес · {fmt_d(sub.daily_claude_used, limits_d['claude'])} день\n"
        f"🔵 DeepSeek: {fmt_m(sub.deepseek_used, limits_m['deepseek'])} мес · {fmt_d(sub.daily_deepseek_used, limits_d['deepseek'])} день\n\n"
        f"🔄 Счётчики: месяц — раз в 30 дней, день — ежедневно"
    )
    return text


def get_referral_text(referral_code: str, bot_username: str, referred_count: int = 0) -> str:
    link = f"https://t.me/{bot_username}?start=ref_{referral_code}"
    return (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Приглашай друзей и получай <b>+10 бонусных запросов</b>\n"
        f"за каждого кто зарегистрируется по твоей ссылке!\n\n"
        f"🔗 Твоя ссылка:\n"
        f"<code>{link}</code>\n\n"
        f"👥 Приглашено друзей: <b>{referred_count}</b>\n\n"
        f"<i>Бонусы тратятся автоматически перед основным лимитом.</i>"
    )
