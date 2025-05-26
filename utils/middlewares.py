from typing import Any, Callable, Awaitable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache

from db_pack.db import get_inactive_user_by_id


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, timelimit = 2):
        super().__init__()
        self.limit = TTLCache(maxsize=10_000, ttl=timelimit)
    
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        command_object = data.get('command')
        if user_id in self.limit and command_object and command_object.command == 'balance':
            await event.answer("Команда 'Баланс' доступна раз в минуту ❗Spam Protect❗")
            return
        else:
            self.limit[user_id] = None
        return await handler(event, data)


class CheckUserActiveMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: Message, data: Dict[str, Any]) -> Any:
        user_id = event.from_user.id
        command_object = data.get('command')
        user = await get_inactive_user_by_id(user_id)

        if user and command_object.command != 'start':
            return await event.answer("Вы были деактивированы. Нажмите /start для повторной активации.")

        return await handler(event, data)