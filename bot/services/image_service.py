from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

IMAGE_DAILY_LIMITS = {"free": 1, "basic": 3, "pro": 10, "ultra": 30}


async def generate_image(prompt: str) -> str:
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    return response.data[0].url
