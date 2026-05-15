import io
from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def transcribe_voice(file_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    audio_file = io.BytesIO(file_bytes)
    audio_file.name = "voice.ogg"
    transcript = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="ru",
    )
    return transcript.text.strip()
