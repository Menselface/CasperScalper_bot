import asyncpg

"""Файл в котором созданы методы для обработки запросов в базу данных"""


class DatabaseAsync:
    def __init__(self, dsn):
        self.dsn = dsn
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=self.dsn)
        async with self.pool.acquire() as connection:
            await connection.execute("SET TIME ZONE 'Europe/Kyiv';")
    
    async def disconnect(self):
        if self.pool is not None:
            await self.pool.close()
    
    async def execute(self, query, *args):
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)
    
    async def fetch(self, query: object, *args: object) -> object:
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)
    
    async def fetchval(self, query, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchval(query, *args)
