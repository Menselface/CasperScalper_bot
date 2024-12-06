from loguru import logger


class UserSessionManager:
    def __init__(self):
        self.sessions = {}
    
    def set_active(self, user_id: int):
        """Отметить пользователя как активного."""
        self.sessions[user_id] = True
        logger.info(f"User {user_id} marked as active.")
    
    def delete_user(self, user_id: int):
        """Удалить пользователя из сессии (сделать неактивным)."""
        if user_id in self.sessions:
            logger.info(f"User {user_id} marked as inactive.")
            del self.sessions[user_id]
    
    def is_active(self, user_id: int) -> bool:
        """Проверить, активен ли пользователь (есть ли он в сессиях)."""
        return user_id in self.sessions

manager_btc = UserSessionManager()
manager_kaspa = UserSessionManager()
manager_sui = UserSessionManager()
manager_pyth = UserSessionManager()