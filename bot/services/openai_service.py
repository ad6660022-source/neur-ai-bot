from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

BASE_SYSTEM_PROMPT = (
    "Ты полезный ИИ-ассистент ChatGPT в Telegram-боте NEUR AI. "
    "Отвечай на русском языке, если пользователь пишет на русском. "
    "Будь точным, информативным и дружелюбным. "
    "Форматируй ответы так, чтобы они хорошо читались в мессенджере."
)


async def ask_chatgpt(
    history: list[dict], mode_prompt: str = ""
) -> tuple[str, int, int]:
    system = BASE_SYSTEM_PROMPT
    if mode_prompt:
        system = system + " " + mode_prompt

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system}] + history,
        max_tokens=2000,
        temperature=0.7,
    )
    text = response.choices[0].message.content
    usage = response.usage
    return text, usage.prompt_tokens, usage.completion_tokens
