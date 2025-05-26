import asyncio

from aiogram import Bot
from loguru import logger

from db_pack.repositories.symbols_for_trade import GetSymbolForTradeRepo
from services.admins.admins_message import AdminsMessageService
from trading.session_manager import (
    UserSessionManager,
    manager_tao,
    manager_dot,
    manager_btc,
    manager_sui,
    manager_pyth,
    manager_kaspa,
)


class SessionRevive: ...


class SessionInspector(SessionRevive):
    SYMBOL_MAP = {"kaspa": "KASUSDT", "btc": "BTCUSDC"}

    @classmethod
    def get_active_symbols_for_user(cls, user_id: int):
        active_symbols = []
        for name, obj in globals().items():
            if name.startswith("manager_") and isinstance(obj, UserSessionManager):
                if obj.is_active(user_id):
                    symbol_key = name.split("_", 1)[1]
                    symbol = cls.SYMBOL_MAP.get(symbol_key, symbol_key + "USDT").upper()
                    active_symbols.append(symbol)

        return active_symbols

    @classmethod
    def get_all_active_sessions(cls, users: list[int]) -> dict[int, list[str]]:
        return {user_id: cls.get_active_symbols_for_user(user_id) for user_id in users}

    @staticmethod
    async def return_inactive_sessions() -> dict[int, list[str]]:

        symbols_for_trade_repo = GetSymbolForTradeRepo()
        db_data = await symbols_for_trade_repo.get_users_with_active_symbols()
        db_users = list(db_data.keys())
        # db_users = [653500570]

        session_data = SessionInspector.get_all_active_sessions(db_users)
        result = {}

        for user_id in db_users:
            db_symbols = db_data[user_id]
            session_symbols = session_data.get(user_id, [])

            missing_symbols = [s for s in db_symbols if s not in session_symbols]

            if missing_symbols:
                result[user_id] = missing_symbols
                logger.warning(
                    f"⚠️ User {user_id} has no active sessions for: {missing_symbols}"
                )

        return result


async def start_session_revival(bot: Bot):
    session_inspector = SessionInspector()
    res = await session_inspector.return_inactive_sessions()
    for user, symbols in res.items():
        msg = f"У пользователя {user} не активны сессии {symbols}"
        admin_service = AdminsMessageService()
        for symbol in symbols:
            await admin_service.send_admin_user_logger_file(user, symbol, bot, msg)
