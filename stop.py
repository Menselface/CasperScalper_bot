from aiogram import Bot
from aiogram.types import Message
from loguru import logger

from db import is_admin_checker, set_user_stop_autobuy, get_all_admins
from first_reg import check_status_of_registration


async def handle_stop(message: Message, bot: Bot):
    user_id = message.from_user.id
    text, registration_to = await check_status_of_registration(message)
    if not registration_to:
        logger.info(
            f"Пользователь {user_id}: - просроченна дата {registration_to}")
        await message.answer(text).as_(bot)
        return
    all_admins = await get_all_admins()
    await set_user_stop_autobuy(user_id=user_id, stop_buy=1)
    await bot.send_message(user_id, "Бот остановлен. Для запуска нажмите /start_trade")
    
    for admin in all_admins:
        try:
            await bot.send_message(admin, f'Пользователь {user_id} - @{message.from_user.username if message.from_user.username else "None"}:\n Остановил покупки ')
        except Exception as e:
            logger.warning(f"Не удалось отправить сообщение админу {admin}\n Ошибка - {e}")
            
        