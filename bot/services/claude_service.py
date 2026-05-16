import base64
import anthropic
from config import settings

kwargs = {"api_key": settings.ANTHROPIC_API_KEY}
if settings.ANTHROPIC_BASE_URL:
    kwargs["base_url"] = settings.ANTHROPIC_BASE_URL

client = anthropic.AsyncAnthropic(**kwargs)

BASE_SYSTEM_PROMPT = (
    "Ты опытный программист-ассистент Claude в Telegram-боте NEUR AI. "
    "Специализируешься на написании кода, отладке, архитектуре систем и технических объяснениях. "
    "Отвечай на русском языке, если пользователь пишет на русском. "
    "Форматирование: ключевые моменты выделяй **жирным**, код пиши в блоках ```язык\n...\n```, "
    "короткий код — в `backticks`. Комментарии и объяснения пиши обычным текстом. "
    "Не используй # заголовки, *курсив*, _подчёркивание_."
)


async def ask_claude(
    history: list[dict], mode_prompt: str = ""
) -> tuple[str, int, int]:
    system = BASE_SYSTEM_PROMPT
    if mode_prompt:
        system = system + " " + mode_prompt

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system,
        messages=history,
    )
    text = response.content[0].text
    usage = response.usage
    return text, usage.input_tokens, usage.output_tokens


async def ask_claude_with_image(
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
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            },
            {"type": "text", "text": caption or "Что на изображении?"},
        ],
    }

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system,
        messages=history + [vision_message],
    )
    text = response.content[0].text
    usage = response.usage
    return text, usage.input_tokens, usage.output_tokens
