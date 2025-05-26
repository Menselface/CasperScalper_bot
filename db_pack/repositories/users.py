import asyncio
import json
from typing import List, Any, Coroutine

from aiogram.types import Message
from loguru import logger

from db_pack import BaseRepositories
from db_pack.repositories.symbols_for_trade import DeleteFromSymbolsForTrade
from utils.decorators import db_safe_call

class UserRepo(BaseRepositories):
    repo = 'users'


class GetUsersRepo(UserRepo):

    @db_safe_call(default_return=[])
    async def all_active_id_from_symbols_for_trade(self) -> List[int]:
        await self.connection_pool()
        result = await self.pool.fetch('SELECT DISTINCT telegram_id FROM symbols_for_trade WHERE start_stop IS true ORDER BY telegram_id')
        return [record['telegram_id'] for record in result]

    @db_safe_call(default_return=[])
    async def all_active_registered_to_status(self):
        await self.connection_pool()
        result = await self.pool.fetch('SELECT telegram_id, registered_to FROM users WHERE registered_to > now()')
        return [record['telegram_id'] for record in result]


    @db_safe_call(default_return=[])
    async def first_user_message_obj(self, user_id: int) -> Message | None:
        await self.connection_pool()
        res = await self.pool.fetchrow("""SELECT message FROM users WHERE telegram_id = $1""", user_id)
        if res:
            message_data = json.loads(res['message'])

            message = Message(**message_data)
            return message
        else:
            logger.info(f"No message found for user_id {user_id}")
            return None

    @db_safe_call(default_return=[])
    async def api_key(self, user_id: int):
        await self.connection_pool()
        return await self.pool.fetchval("SELECT api_key FROM users WHERE telegram_id = $1", user_id)

    @db_safe_call(default_return=[])
    async def secret_key(self, user_id: int):
        await self.connection_pool()
        return await self.pool.fetchval("SELECT secret_key FROM users WHERE telegram_id = $1", user_id)

    @db_safe_call(default_return=[])
    async def get_all_admins(self):
        await self.connection_pool()
        result = await self.pool.fetch('SELECT telegram_id FROM users WHERE is_admin = true')
        return [record['telegram_id'] for record in result]

    @db_safe_call(default_return=[])
    async def user_is_admin_return(self, user_id) -> bool:
        await self.connection_pool()
        return await self.pool.fetch('SELECT is_admin FROM users WHERE telegram_id = $1', user_id)

class UpdateUserRepo(UserRepo):

    @db_safe_call(default_return=[])
    async def user_first_message_obj(self, user_id: int, message: str):
        await self.connection_pool()
        await self.pool.fetch("""UPDATE users SET message = $2 WHERE telegram_id = $1 """, user_id, message)