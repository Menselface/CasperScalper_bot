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
    await message.answer(f"Ваша подписка действует до {registered_to}\nДля продления свяжитесь с @AlisaStrange").as_(bot)