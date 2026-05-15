from openai import AsyncOpenAI
from config import settings

# DeepSeek uses OpenAI-compatible API
client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
)

SYSTEM_PROMPT = (
    "Ты полезный ИИ-ассистент DeepSeek в Telegram-боте NEUR AI. "
    "Отвечай на русском языке, если пользователь пишет на русском. "
    "Специализируйся на математике, программировании и логических задачах. "
    "Давай точные, структурированные и детальные технические ответы. "
    "Форматируй ответы для удобного чтения в мессенджере."
)


async def ask_deepseek(history: list[dict]) -> tuple[str, int, int]:
    """Returns (response_text, prompt_tokens, completion_tokens)"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=2000,
        temperature=0.7,
    )

    text = response.choices[0].message.content
    usage = response.usage

    return text, usage.prompt_tokens, usage.completion_tokens
