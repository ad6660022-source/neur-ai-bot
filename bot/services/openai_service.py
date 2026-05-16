import base64
from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

BASE_SYSTEM_PROMPT = (
    "Ты полезный ИИ-ассистент ChatGPT в Telegram-боте NEUR AI. "
    "Отвечай на русском языке, если пользователь пишет на русском. "
    "Будь точным, информативным и дружелюбным. "
    "Пиши обычным текстом без markdown-форматирования: не используй **, *, _, __, #, ##. "
    "Для структуры используй только обычные символы: дефис, цифры, переносы строк."
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


async def ask_chatgpt_with_image(
    image_bytes: bytes,
    caption: str,
    history: list[dict],
    mode_prompt: str = "",
) -> tuple[str, int, int]:
    system = BASE_SYSTEM_PROMPT
    if mode_prompt:
        system = system + " " + mode_prompt

    b64 = base64.b64encode(image_bytes).decode()
    vision_message = {
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": caption or "Что на изображении?"},
        ],
    }

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system}] + history + [vision_message],
        max_tokens=2000,
        temperature=0.7,
    )
    text = response.choices[0].message.content
    usage = response.usage
    return text, usage.prompt_tokens, usage.completion_tokens
