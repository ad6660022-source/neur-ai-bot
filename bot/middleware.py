from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database.crud import get_user


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_obj = data.get("event_from_user")
        if user_obj:
            db_user = await get_user(user_obj.id)
            if db_user and db_user.is_banned:
                if isinstance(event, CallbackQuery):
                    await event.answer("⛔ Ваш аккаунт заблокирован.", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer("⛔ Ваш аккаунт заблокирован администратором.")
                return
        return await handler(event, data)
