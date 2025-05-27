from loguru import logger

from infrastructure.db_pack.db import (
    delete_inactive_users,
    insert_to_inactive,
    get_all_inactive_users,
    delete_user_from_inactive_table,
    user_update,
    get_inactive_user_by_id_trial_status,
)
from infrastructure.db_pack.repositories import GetUsersRepo
from infrastructure.db_pack.repositories.symbols_for_trade import (
    DeleteFromSymbolsForTrade,
)


async def remove_inactive_users():
    inactive_users = await get_all_inactive_users()
    await delete_from_symbols_for_trade_users()
    if inactive_users:
        await insert_to_inactive(inactive_users)
        await delete_inactive_users()
        logger.info(f"Пользователи перенесены: {inactive_users}")
    else:
        logger.info("Нет неактивных пользователей для переноса.")


async def check_inactive_user(user_id: int):
    trial_promo = await get_inactive_user_by_id_trial_status(user_id)
    if trial_promo:
        await user_update(user_id, trial_promo=trial_promo)
        await delete_user_from_inactive_table(user_id)


async def delete_from_symbols_for_trade_users():
    user_repo = GetUsersRepo()
    rs_users = await user_repo.all_active_registered_to_status()
    rs_symbols = await user_repo.all_active_id_from_symbols_for_trade()
    for user in rs_symbols:
        if user not in rs_users:
            logger.info(f"User {user} deleted from Symbols for trade table")
            await DeleteFromSymbolsForTrade().delete_user_if_not_in_user_table(user)
