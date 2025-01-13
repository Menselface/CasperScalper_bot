import time

from aiogram import BaseMiddleware
from aiogram.types import Message


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.limits = {}
        
    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id
        current_time = time.time()
        command_object = data.get('command')
        if command_object and command_object.command == 'balance':
            if user_id in self.limits:
                last_called = self.limits[user_id]
                if current_time - last_called < 60:
                    await event.answer("Вы можете вызывать этот хендлер не чаще, чем раз в минуту.")
                    return
        else:
            if user_id in self.limits:
                last_called = self.limits[user_id]
                if current_time - last_called < 2:
                    await event.answer("Вызов ограничен раз в 2 секунды.")
                    return
        
        self.limits[user_id] = current_time
        return await handler(event, data)