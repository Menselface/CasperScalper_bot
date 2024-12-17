import asyncio
import os
import shutil

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from loguru import logger

from db import is_admin_checker, set_reset_autobuy, all_users_with_reset_status, get_first_message
from keyboards import admin_keyboard
from trading.session_manager import manager_sui, manager_pyth, manager_dot
from trading.start_trade import user_restart_from_admin_panel
from trading.trading_btc import manager_btc
from trading.trading_kas import manager_kaspa

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
            "Команда <b>ОБНОВИТЬ</b> переведет всех, у кого запущена торговля, в статус 1.\n"
            "Команда <b>КОЛБАСА</b> запустит всех пользователям со статусом 1.\n\n"
            "НАЧИНАЙ - жми <b>Обновить</b>"
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
    active_users_btc = manager_btc.sessions
    active_users_kaspa = manager_kaspa.sessions
    active_users_sui = manager_sui.sessions
    active_users_pyth = manager_pyth.sessions
    active_users_dot = manager_dot.sessions
    hello_everybody = active_users_kaspa | active_users_btc | active_users_sui | active_users_pyth | active_users_dot
    logger.info(f"{hello_everybody} переведены в статус 1")
    await bot.send_message(user_id,
                           f"1. К обновлению готов!\n{hello_everybody.keys()} переведены в статус 1\n\n"
                           "2. Останови Бота на сервере:\n"
                           "➡️ CTRL+C или CTRL+Z"
                           )

    for user in hello_everybody.keys():
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
        task = asyncio.create_task(user_restart_from_admin_panel(res, bot))
        tasks.append(task)
    await bot.send_message(user_id, "Все пользователи запущены!")
    await asyncio.gather(*tasks)


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
    