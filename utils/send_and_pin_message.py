import asyncio
from datetime import datetime

from aiogram import Bot
from asyncpg.pgproto.pgproto import timedelta
from loguru import logger

from db import get_all_id_with_registered_to_status, get_first_message
from statistic import handle_stats
from utils.statistic_for_admins import get_statistic_for_admin


async def send_and_pin(bot: Bot):
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)
    all_users = await get_all_id_with_registered_to_status(today)
    for user in all_users:
        res = await get_first_message(user)
        message = await handle_stats(res, from_statistic=True, from_yesterday=yesterday)
        try:
            day_statistic_message = await bot.send_message(user, message)
            await bot.pin_chat_message(user, day_statistic_message.message_id, disable_notification=True)
            logger.info(f"Message send and pin for user {user}")
        except Exception as e:
            logger.warning(f"Ошибка при отправке/закреплении сообщения: {e} to user {user}")
    await get_statistic_for_admin(bot)