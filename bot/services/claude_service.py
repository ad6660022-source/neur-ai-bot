import anthropic
from config import settings

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = (
    "Ты полезный ИИ-ассистент Claude в Telegram-боте NEUR AI. "
    "Отвечай на русском языке, если пользователь пишет на русском. "
    "Специализируйся на глубоком анализе, исследованиях и точных ответах. "
    "Форматируй ответы для удобного чтения в мессенджере."
)


async def ask_claude(history: list[dict]) -> tuple[str, int, int]:
    """Returns (response_text, prompt_tokens, completion_tokens)"""
    response = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=history,
    )

    text = response.content[0].text
    usage = response.usage

    return text, usage.input_tokens, usage.output_tokens
