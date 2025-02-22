from aiogram import Bot
from loguru import logger

from first_reg import check_status_of_registration
from trading.db_querys.db_symbols_for_trade_methods import update_user_symbol_data


async def validate_user_status(message, user_id, manager, symbol, bot: Bot,):
    _, status = await check_status_of_registration(message)
    if not status:
        await bot.send_message(user_id, text=f"Модуль {symbol} остановлен, закончилась подписка\n\nСвяжитесь с поддержкой 📌@AlisaStrange")
        manager.delete_user(user_id)
        logger.info(f"Модуль {symbol} остановлен, закончилась подписка {user_id}!")
        await update_user_symbol_data(user_id, symbol, start_stop=False)
        return True
    return False