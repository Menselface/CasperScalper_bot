from contracts import IMessageStore, UserId, MessageId
from redis_client import RedisClient
from keys import message_id_key


class RedisMessageStore(IMessageStore):
    def __init__(self, redis: RedisClient):
        self.redis = redis

    async def save(
        self, user_id: UserId, message_id: MessageId, ttl_seconds: int = 3600
    ) -> None:
        key = message_id_key(user_id)
        success = await self.redis.set_json(key, int(message_id), expire=ttl_seconds)
        if not success:
            raise RuntimeError(f"Failed to save message_id for user {user_id}")

    async def get(self, user_id: UserId) -> MessageId | None:
        key = message_id_key(user_id)
        result = await self.redis.get_json(key)
        return MessageId(result) if result is not None else None
