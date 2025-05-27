from contracts import UserId


def message_id_key(user_id: UserId) -> str:
    return f"bot:message_id:{user_id}"
