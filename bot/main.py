import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.db import init_db
from handlers import start, menu, chatgpt, claude, deepseek, subscription, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting NEUR AI Bot...")

    await init_db()

    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register all routers
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(subscription.router)
    dp.include_router(chatgpt.router)
    dp.include_router(claude.router)
    dp.include_router(deepseek.router)
    dp.include_router(admin.router)

    # Fallback handler for unhandled messages
    @dp.message()
    async def fallback_handler(message):
        from keyboards import bottom_keyboard
        await message.answer(
            "⚠️ Выберите нейросеть из меню, чтобы начать общение.\n"
            "Используйте кнопку ниже или напишите /menu.",
            reply_markup=bottom_keyboard()
        )

    logger.info("Bot is running!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
