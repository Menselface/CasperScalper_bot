from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from infrastructure.db_pack.db import get_inactive_user_by_id


class CheckUserActiveMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        command_object = data.get("command")
        user = await get_inactive_user_by_id(user_id)

        if user and command_object.command != "start":
            return await event.answer(
                "Вы были деактивированы. Нажмите /start для повторной активации."
            )

        return await handler(event, data)
