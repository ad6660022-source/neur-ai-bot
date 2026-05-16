import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.db import init_db
from middleware import BanCheckMiddleware
from scheduler import setup_scheduler
from handlers import start, menu, chatgpt, claude, deepseek, subscription, admin
from handlers import modes, switcher, history  # image disabled temporarily

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
    dp.include_router(chatgpt.router)
    dp.include_router(claude.router)
    dp.include_router(deepseek.router)
    dp.include_router(admin.router)

    # Fallback MUST be in its own router included last —
    # a bare @dp.message() fires before sub-router handlers in aiogram 3.x.
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


async def run_polling(bot: Bot, dp: Dispatcher):
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Running in POLLING mode")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def run_webhook(bot: Bot, dp: Dispatcher):
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
    await bot.set_webhook(url=webhook_url, secret_token=settings.WEBHOOK_SECRET)
    logger.info("Webhook set: %s", webhook_url)

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
    ).register(app, path=settings.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.PORT)
    await site.start()
    logger.info("Running in WEBHOOK mode on port %d", settings.PORT)

    await asyncio.Event().wait()  # run forever


async def main():
    logger.info("Starting NEUR AI Bot...")
    await init_db()

    bot = Bot(token=settings.BOT_TOKEN)
    dp = build_dispatcher()

    setup_scheduler(bot)

    if settings.WEBHOOK_URL:
        await run_webhook(bot, dp)
    else:
        await run_polling(bot, dp)


if __name__ == "__main__":
    asyncio.run(main())
