from aiogram import Bot
from loguru import logger

from config import ADMIN_ID, ADMIN_ID2

from bot.handlers.start import check_status_of_registration
from infrastructure.db_pack.db import user_get_any
from trading.db_querys.db_symbols_for_trade_methods import update_user_symbol_data


async def validate_user_status(
    message,
    user_id,
    manager,
    symbol,
    bot: Bot,
):
    _, status = await check_status_of_registration(message)
    admins = [ADMIN_ID, ADMIN_ID2]

    if not status:
        await bot.send_message(
            user_id,
            text=f"Модуль {symbol} остановлен, закончилась подписка\n\nСвяжитесь с поддержкой ➡️ @Infinty_Support",
        )
        manager.delete_user(user_id)
        logger.info(f"Модуль {symbol} остановлен, закончилась подписка {user_id}!")
        await update_user_symbol_data(user_id, symbol, start_stop=False)
        await update_user_symbol_data(user_id, symbol, info_no_usdt=0)
        await update_user_symbol_data(user_id, symbol, limit_message=0)
        user_name = await user_get_any(user_id, username="username")
        if user_name == "Нет":
            user_name = await user_get_any(user_id, first_name="first_name")
        end_of_subscription = await user_get_any(user_id, registered_to="registered_to")
        for admin in admins:
            try:
                await bot.send_message(
                    admin,
                    f"Торговая пара {symbol} у пользователя :\n{user_id} - {user_name} - была остановлена\n\n Дата окончания подписки - {end_of_subscription}",
                )
            except Exception as e:
                logger.warning(f"Message not delivered to admin, reason - {e}")
        return True
    return False
