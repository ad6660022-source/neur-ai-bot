import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.db import init_db
from middleware import BanCheckMiddleware
from scheduler import setup_scheduler
from handlers import start, menu, chatgpt, claude, subscription, admin, support
from handlers import modes, switcher, history  # image and deepseek disabled

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())

    # Order matters: shared handlers first, model-specific last
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(modes.router)       # start_chat:X / set_mode:X:Y / change_mode:X
    dp.include_router(switcher.router)    # switch_to:X / stop_chat / back_to_menu
    dp.include_router(history.router)     # save_chat / my_chats / load/del chat
    dp.include_router(subscription.router)
    dp.include_router(support.router)
    dp.include_router(chatgpt.router)
    dp.include_router(claude.router)
    dp.include_router(admin.router)

    fallback_router = Router()

    @fallback_router.message()
    async def fallback_handler(message):
        from keyboards import bottom_keyboard
        await message.answer(
            "⚠️ Выбери нейросеть из меню чтобы начать общение.\n"
            "Используй кнопку ниже или напиши /menu.",
            reply_markup=bottom_keyboard(),
        )

    dp.include_router(fallback_router)
    return dp


async def main():
    logger.info("Starting NEUR AI Bot...")
    await init_db()

    bot = Bot(token=settings.BOT_TOKEN)
    dp = build_dispatcher()
    setup_scheduler(bot)

    from aiohttp import web
    from webapp_api import setup_webapp_routes

    app = web.Application()
    setup_webapp_routes(app, bot)

    if settings.WEBHOOK_URL:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
        await bot.set_webhook(url=webhook_url, secret_token=settings.WEBHOOK_SECRET)
        logger.info("Webhook set: %s", webhook_url)
        SimpleRequestHandler(
            dispatcher=dp, bot=bot, secret_token=settings.WEBHOOK_SECRET
        ).register(app, path=settings.WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
    else:
        logger.info("Running in POLLING mode")
        await bot.delete_webhook(drop_pending_updates=True)

        async def _poll():
            try:
                await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            except Exception as exc:
                logger.critical("Polling crashed: %s", exc, exc_info=True)

        asyncio.create_task(_poll())

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.PORT)
    await site.start()
    logger.info("Server running on port %d", settings.PORT)

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
