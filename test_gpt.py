import asyncio
import os
import sys

# Add bot dir to path
sys.path.append(os.path.join(os.path.dirname(__file__), "bot"))

from bot.config import settings
from bot.services.openai_service import ask_chatgpt

async def main():
    print(f"Key used: {settings.OPENAI_API_KEY[:10]}...")
    try:
        response, p_tokens, c_tokens = await ask_chatgpt([{"role": "user", "content": "Hello, this is a test."}])
        print("Success:", response)
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    asyncio.run(main())
