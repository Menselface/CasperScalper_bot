from aiogram.filters.command import Command

from aiogram import Bot, Router
from aiogram.types import Message

from loguru import logger

from db_pack.db import get_registered_to
from bot.handlers.start import check_status_of_registration


subscription_info_router = Router(name=__name__)


@subscription_info_router.message(Command("subs"))
async def handle_subs(message: Message, bot: Bot):
    user_id = message.from_user.id
    text, registration_to = await check_status_of_registration(message)
    title = "Ваша подписка действует до:"
    if not registration_to:
        logger.info(f"Пользователь {user_id}: - просроченна дата {registration_to}")
        title = "Ваша регистрация закончилась"
    registered_to = await get_registered_to(user_id)
    registered_to = registered_to.strftime("%d.%m.%Y, %H-%M")
    await message.answer(
        f"{title} <b>{registered_to}</b>\n\n➡️ <a href='https://telegra.ph/Tarify-NA-ISPOLZOVANIE-INFINITY-Bot-Pro-01-16'>[Тарифы]</a>\n\nКошелек для оплаты <b>USDT(TRC20)</b>:\n\n<code>TXjBKZSMXyqsyBX7AL9GHhHpvo6oNN4iWt</code>\n\n⬆️ ️Нажмите чтобы скопировать ⬆️\n\nСбросьте данные об оплате: @Infinty_Support\n"
    ).as_(bot)
