from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
)

BASE_SYSTEM_PROMPT = (
    "Ты полезный ИИ-ассистент DeepSeek в Telegram-боте NEUR AI. "
    "Отвечай на русском языке, если пользователь пишет на русском. "
    "Специализируйся на математике, программировании и логических задачах. "
    "Давай точные, структурированные и детальные технические ответы. "
    "Форматируй ответы для удобного чтения в мессенджере."
)


async def ask_deepseek(
    history: list[dict], mode_prompt: str = ""
) -> tuple[str, int, int]:
    system = BASE_SYSTEM_PROMPT
    if mode_prompt:
        system = system + " " + mode_prompt

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system}] + history,
        max_tokens=2000,
        temperature=0.7,
    )
    text = response.choices[0].message.content
    usage = response.usage
    return text, usage.prompt_tokens, usage.completion_tokens
