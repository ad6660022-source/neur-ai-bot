from database.crud import PLAN_LIMITS, PLAN_PRICES, PLAN_EMOJI

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
        "model": "Claude 3.5 Sonnet",
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
            "Передовая модель от китайской команды DeepSeek. "
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
        f"🟣 <b>Claude</b> (Sonnet 3.5) — аналитик и исследователь\n"
        f"🔵 <b>DeepSeek</b> (V3) — технический и математический\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Выбери нейросеть в меню и начни общение!\n\n"
        f"💡 <i>Используй /menu для выбора ИИ\n"
        f"или /plans для просмотра тарифов</i>"
    )


def get_ai_selection_text() -> str:
    text = "🤖 <b>Выбери нейросеть для работы</b>\n\n"
    text += "Ниже — краткое описание каждой модели:\n\n"

    for key, info in AI_DESCRIPTIONS.items():
        text += f"{info['emoji']} <b>{info['name']}</b> — {info['tagline']}\n"
        text += f"<i>{info['description']}</i>\n"
        text += "<b>Лучше всего подходит для:</b>\n"
        for item in info["best_for"]:
            text += f"  {item}\n"
        text += "\n"

    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "👇 Нажми кнопку, чтобы выбрать ИИ:"
    return text


def get_plans_text() -> str:
    text = "💳 <b>Тарифные планы NEUR AI</b>\n\n"

    plans_info = {
        "free": {
            "name": "Бесплатный",
            "price_label": "0 ₽ / мес",
            "features": [
                "🟢 ChatGPT: 5 запросов/мес",
                "🔵 DeepSeek: 10 запросов/мес",
                "🟣 Claude: недоступен",
            ],
        },
        "basic": {
            "name": "Basic",
            "price_label": "~450 ₽ / мес",
            "features": [
                "🟢 ChatGPT: 30 запросов/мес",
                "🔵 DeepSeek: 50 запросов/мес",
                "🟣 Claude: недоступен",
            ],
        },
        "pro": {
            "name": "Pro",
            "price_label": "~900 ₽ / мес",
            "features": [
                "🟢 ChatGPT: 80 запросов/мес",
                "🟣 Claude: 10 запросов/мес",
                "🔵 DeepSeek: 150 запросов/мес",
            ],
        },
        "ultra": {
            "name": "Ultra",
            "price_label": "~1800 ₽ / мес",
            "features": [
                "🟢 ChatGPT: 200 запросов/мес",
                "🟣 Claude: 30 запросов/мес",
                "🔵 DeepSeek: ∞ безлимит",
            ],
        },
    }

    for plan_key, plan in plans_info.items():
        emoji = PLAN_EMOJI.get(plan_key, "")
        price = PLAN_PRICES.get(plan_key, 0)
        text += f"{emoji} <b>{plan['name']}</b> — <b>{plan['price_label']}</b>\n"
        for feature in plan["features"]:
            text += f"  {feature}\n"
        text += "\n"

    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "📩 Для активации подписки напиши /buy\n"
    text += "или обратись к администратору"
    return text


def get_usage_text(sub) -> str:
    from database.crud import PLAN_LIMITS, PLAN_EMOJI
    plan = sub.plan
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    emoji = PLAN_EMOJI.get(plan, "")

    def fmt(used, limit):
        if limit == -1:
            return f"{used} / ∞"
        return f"{used} / {limit}"

    text = (
        f"📊 <b>Ваш профиль</b>\n\n"
        f"{emoji} Тариф: <b>{plan.upper()}</b>\n\n"
        f"<b>Запросы в этом месяце:</b>\n"
        f"🟢 ChatGPT: {fmt(sub.chatgpt_used, limits['chatgpt'])}\n"
        f"🟣 Claude:   {fmt(sub.claude_used, limits['claude'])}\n"
        f"🔵 DeepSeek: {fmt(sub.deepseek_used, limits['deepseek'])}\n\n"
        f"🔄 Счётчики сбрасываются каждые 30 дней"
    )
    return text
