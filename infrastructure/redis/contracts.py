from typing import NewType, Protocol, Optional

UserId = NewType("UserId", int)
MessageId = NewType("MessageId", int)


class IMessageStore(Protocol):
    async def save(
        self, user_id: UserId, message_id: MessageId, ttl_seconds: int = 3600
    ) -> None: ...
    async def get(self, user_id: UserId) -> Optional[MessageId]: ...
