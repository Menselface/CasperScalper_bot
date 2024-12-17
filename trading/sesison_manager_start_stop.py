from loguru import logger

from trading.db_querys.db_symbols_for_trade_methods import get_symbols_for_keyboard


class UserSessionManagerStartStop:
    def __init__(self):
        self.sessions = {}
    
    async def fill_info_from_db(self, user_id: int):
        btc_status = await get_symbols_for_keyboard(user_id, "BTCUSDC")
        kaspa_status = await get_symbols_for_keyboard(user_id, "KASUSDT")
        sui_status = await get_symbols_for_keyboard(user_id, "SUIUSDT")
        pyth_status = await get_symbols_for_keyboard(user_id, "PYTHUSDT")
        dot_status = await get_symbols_for_keyboard(user_id, "DOTUSDT")
        self.sessions[user_id] = [
            {"BTCUSDC": btc_status},
            {"KASUSDT": kaspa_status},
            {"SUIUSDT": sui_status},
            {"PYTHUSDT": pyth_status},
            {"DOTUSDT": dot_status}
        ]
        logger.info(f"User {user_id} marked as active.")
    
    def change_status(self, user_id: int, symbol: str):
        if user_id not in self.sessions:
            raise ValueError(f"Session for user {user_id} not found.")
        
        for item in self.sessions[user_id]:
            if symbol in item:
                item[symbol] = not item[symbol]
                break
        
        logger.info(f"User {user_id}: status for {symbol} updated to {item[symbol]}.")
    
    async def get_session_data(self, user_id: int):
        """Возвращает данные пользователя, если их нет — создает сессию."""
        if user_id not in self.sessions:
            logger.info(f"No session found for user {user_id}. Initializing session.")
            await self.fill_info_from_db(user_id)
        return self.sessions[user_id]
    
    async def remove_user(self, user_id: int):
        """Удаляет пользователя из сессии."""
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"User {user_id} removed from sessions.")
        else:
            logger.info(f"Attempted to remove non-existent session for user {user_id}.")


user_start_stop = UserSessionManagerStartStop()
