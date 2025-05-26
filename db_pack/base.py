

from config import db_async


class BaseRepositories:
    def __init__(self):
        self.pool = db_async

    async def connection_pool(self):
        if self.pool.pool is None:
            await self.pool.connect()