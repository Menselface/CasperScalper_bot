from aiogram import Bot
from aiogram.types import Message

from loguru import logger

from db import get_registered_to
from first_reg import check_status_of_registration


async def handle_subs(message: Message, bot: Bot):
    user_id = message.from_user.id
    text, registration_to = await check_status_of_registration(message)
    if not registration_to:
        logger.info(
            f"Пользователь {user_id}: - просроченна дата {registration_to}")
        await message.answer(text).as_(bot)
        return
    registered_to = await get_registered_to(user_id)
    registered_to = registered_to.strftime('%d.%m.%Y, %H-%M')
    await message.answer(f"Ваша подписка действует до <b>{registered_to}</b>\n\n➡️ <a href='https://t.me/TradingForAllEasy/14'>[Тарифы]</a>\nКошелек для оплаты USDT ❗TRC20❗:\n\n<code>TXjBKZSMXyqsyBX7AL9GHhHpvo6oNN4iWt</code>\n\n⬆️ ️Нажми чтобы скопировать ⬆️\n\nСбросьте данные об оплате - @RomaKnyazeff").as_(bot)