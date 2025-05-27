from redis.asyncio import Redis, RedisError
from loguru import logger
import json
from typing import Any


class RedisClient:
    def __init__(self, redis: Redis, prefix: str = "bot:"):
        self.redis = redis
        self.prefix = prefix

    def _prefixed(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def set_json(self, key: str, value: Any, expire: int = 3600) -> bool:
        try:
            return await self.redis.set(
                self._prefixed(key), json.dumps(value), ex=expire
            )
        except RedisError as e:
            logger.warning(f"Redis SET failed: {e}")
            return False

    async def get_json(self, key: str):
        try:
            raw = await self.redis.get(self._prefixed(key))
            return json.loads(raw) if raw else None

        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Redis GET failed: {e}")

    async def close(self):
        await self.redis.close()
