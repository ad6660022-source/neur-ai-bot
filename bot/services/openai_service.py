from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "Ты полезный ИИ-ассистент ChatGPT в Telegram-боте NEUR AI. "
    "Отвечай на русском языке, если пользователь пишет на русском. "
    "Будь точным, информативным и дружелюбным. "
    "Форматируй ответы так, чтобы они хорошо читались в мессенджере."
)


async def ask_chatgpt(history: list[dict]) -> tuple[str, int, int]:
    """Returns (response_text, prompt_tokens, completion_tokens)"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=2000,
        temperature=0.7,
    )

    text = response.choices[0].message.content
    usage = response.usage

    return text, usage.prompt_tokens, usage.completion_tokens
