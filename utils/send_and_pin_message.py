import asyncio
import re
from datetime import datetime

from aiogram import Bot
from asyncpg.pgproto.pgproto import timedelta
from loguru import logger

from infrastructure.db_pack.db import (
    get_all_id_with_registered_to_status,
    get_first_message,
)
from bot.handlers.statistic import handle_stats
from utils.statistic_for_admins import get_statistic_for_admin


async def send_and_pin(bot: Bot):
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)
    date_to = today + timedelta(days=11)
    all_users = await get_all_id_with_registered_to_status(date_to)
    chat_link_message = '➡️  <a href="https://t.me/+SlFS19D7cdc3MzQy">Наш ЧАТ</a>  ⬅️'
    support_community_message = "❗️ Спасибо, что делитесь своими результатами!\nПерешлите статистику ☝️ в наш чат, поддержите комьюнити"

    for user in all_users:
        res = await get_first_message(user)
        day, month = await handle_stats(
            res, from_statistic=True, from_yesterday=yesterday
        )

        try:
            day_statistic_message = await bot.send_message(
                user, day, disable_notification=True
            )
            await bot.pin_chat_message(
                user, day_statistic_message.message_id, disable_notification=True
            )
            await bot.send_message(
                user,
                chat_link_message,
                disable_notification=True,
                disable_web_page_preview=True,
            )
            await bot.send_message(
                user, support_community_message, disable_notification=True
            )

            logger.info(f"Message send and pin for user {user}")
        except Exception as e:
            logger.warning(
                f"Ошибка при отправке/закреплении сообщения: {e} to user {user}"
            )

    await get_statistic_for_admin(bot)


async def send_and_pin_month(bot: Bot):
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)
    date_to = today + timedelta(days=11)
    all_users = await get_all_id_with_registered_to_status(date_to)
    messages = {}
    for user in all_users:
        res = await get_first_message(user)
        day, month = await handle_stats(
            res, from_statistic=True, from_yesterday=yesterday
        )
        messages[user] = await format_profit_message(month)

    await asyncio.sleep(65)

    tasks = []
    for user, text in messages.items():
        tasks.append(bot.send_message(user, text, disable_notification=True))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for user, result in zip(all_users, results):
        if isinstance(result, Exception):
            logger.warning(
                f"Ошибка при отправке/закреплении сообщения для пользователя {user}: {result}"
            )


async def format_profit_message(raw_text: str):
    months = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }

    month_name = months[datetime.today().month]

    total_deals_match = re.search(r"<b>Всего:\nКоличество сделок: (\d+)", raw_text)
    total_profit_match = re.search(r"Прибыль: ([\d.]+) USDT</b>", raw_text)

    deals_count = total_deals_match.group(1) if total_deals_match else "0"
    profit_amount = total_profit_match.group(1) if total_profit_match else "0.0"

    return (
        f"<b>Сделок за {month_name}: {deals_count}\n"
        f"Прибыль за {month_name}: {profit_amount} USDT</b>"
    )
