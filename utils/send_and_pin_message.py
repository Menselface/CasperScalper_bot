import asyncio
from datetime import datetime
from pprint import pprint
from loguru import logger

from aiogram import Bot
from asyncpg.pgproto.pgproto import timedelta

from db import get_all_id_with_registered_to_status, closed_orders_for_pin_message


async def send_and_pin(bot: Bot):
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)
    all_users = await get_all_id_with_registered_to_status(today)
    for user in all_users:
        result, deals_length = await closed_orders_for_pin_message(user_id=user, status=2, now=yesterday)
        message = (f"{yesterday.strftime('%d.%m.%Y')}\n"
                   f"Количество сделок:{deals_length}\n"
                   f"Прибыль: {result:.2f} USDT")
        try:
            day_statistic_message = await bot.send_message(user, message)
            await bot.pin_chat_message(user, day_statistic_message.message_id, disable_notification=True)
            logger.info(f"Message send and pin for user {user}")
        except Exception as e:
            logger.warning(f"Ошибка при отправке/закреплении сообщения: {e} to user {user}")
        
        

    
    