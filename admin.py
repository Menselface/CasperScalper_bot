import asyncio
import os
import shutil

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from loguru import logger

from db import is_admin_checker, set_reset_autobuy, all_users_with_reset_status, get_first_message
from keyboards import admin_keyboard
from trading import is_working, handle_autobuy

admin_router = Router()


async def handle_admin(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    if not user_id in all_admins:
        return
    
    mes = await message.answer("Привет админ ✌️", reply_markup=admin_keyboard())
    await state.update_data(message=mes.message_id)


@admin_router.callback_query(F.data == 'refreshing')
async def refresh_all_users(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    res = await state.get_data()
    message_to_edit = res.get('message')
    if user_id not in all_admins:
        return
    mes = await bot.edit_message_text(
        chat_id=user_id,
        message_id=message_to_edit,
        text=(
            "Обновимся?\n"
            "Команда <b>ОБНОВИТЬ</b> переведет всех, у кого запущен автобай, в статус 1.\n"
            "Команда <b>КОЛБАСА</b> запустит автоматически автобай всем пользователям со статусом 1.\n\n"
            "<b>Порядок обновления:</b>\n"
            "1. На сервер залей обновление с ГитХаб — (дай команду <code>git pull origin master</code>)\n"
            "2. Нажми кнопку <b>ОБНОВИТЬ</b> ⬇️\n"
            "3. Останови Бота на сервере — <code>Ctrl+C</code>\n"
            "4. Запусти Бота — <code>python3 main.py</code>\n"
            "5. Нажми <b>КОЛБАСА</b>"
        ),
        reply_markup=admin_keyboard(level=1))
    await state.update_data(message=mes.message_id)

@admin_router.callback_query(F.data == 'back_to_admin')
async def refresh_all_users(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    result = await state.get_data()
    message_to_edit = result.get('message')
    if not user_id in all_admins:
        return
    await bot.edit_message_text(chat_id=user_id,
                                message_id=message_to_edit,
                                text="Привет админ ✌️",
                                reply_markup=admin_keyboard(level=0))
    
    
@admin_router.callback_query(F.data == 'refresh')
async def refresh_all_users(message: Message, bot: Bot):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    if not user_id in all_admins:
        return
    active_users = is_working.user_autobuy_status
    logger.info(f"{active_users} переведены в статус 1")
    await bot.send_message(user_id,
                           "1. К обновлению готов!\n"
                           "2. Останови Бота на сервере:\n"
                           "➡️ CTRL+C или CTRL+Z"
                           )

    for user in active_users:
        await set_reset_autobuy(user, 1)


@admin_router.callback_query(F.data == 'restart')
async def rstart_autobuy(message: Message, bot: Bot):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    if not user_id in all_admins:
        return
    await bot.send_message(user_id, 'Колбаса сработала - 👍 Бот запущен !')
    
    active_users = await all_users_with_reset_status()
    
    tasks = []
    
    for user in active_users:
        res = await get_first_message(user)
        task = asyncio.create_task(handle_autobuy(res, bot))
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    await bot.send_message(user_id, "Все пользователи запущены!")


@admin_router.callback_query(F.data == 'get_logs')
async def get_logs(message: Message, bot: Bot):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    if not user_id in all_admins:
        return
    log_file = f'logs/logers.log'
    temp_log_file = f'logs/logers_сopy.log'
    shutil.copy(log_file, temp_log_file)
    user_agreements = FSInputFile('logs/logers_сopy.log', filename='logers_сopy.log')
    try:
        await bot.send_document(user_id, user_agreements)
        os.remove(temp_log_file)
    except Exception as e:
        logger.warning(f"{e}")
        await message.answer(f"Не могу скинуть файл {e}")
    