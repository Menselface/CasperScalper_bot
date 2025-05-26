from datetime import datetime, timedelta

from aiogram import Bot, Router, F, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from db_pack.db import (
    is_admin_checker,
    set_reset_autobuy,
    get_all_id_with_registered_to_status,
)
from bot.keyboards.keyboards import admin_keyboard
from services.admins.admins_checker import AdminChecker
from services.admins.admins_message import AdminsMessageService
from services.restart_user_service import RestartUserService
from trading.session_manager import manager_sui, manager_pyth, manager_dot
from trading.trading_btc import manager_btc
from trading.trading_kas import manager_kaspa

admin_router = Router(name=__name__)


@admin_router.message(F.text.lower() == "админ")
async def handle_admin(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    if not user_id in all_admins:
        return

    mes = await message.answer("Привет админ ✌️", reply_markup=admin_keyboard())
    await state.update_data(message=mes.message_id)


@admin_router.callback_query(F.data == "refreshing")
async def refresh_all_users(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    res = await state.get_data()
    message_to_edit = res.get("message")
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
        reply_markup=admin_keyboard(level=1),
    )
    await state.update_data(message=mes.message_id)


@admin_router.callback_query(F.data == "back_to_admin")
async def refresh_all_users(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    result = await state.get_data()
    message_to_edit = result.get("message")
    if not user_id in all_admins:
        return
    await bot.edit_message_text(
        chat_id=user_id,
        message_id=message_to_edit,
        text="Привет админ ✌️",
        reply_markup=admin_keyboard(level=0),
    )


@admin_router.callback_query(F.data == "refresh")
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
    active_users_tao = manager_dot.sessions
    hello_everybody = (
        active_users_kaspa
        | active_users_btc
        | active_users_sui
        | active_users_pyth
        | active_users_dot
        | active_users_tao
    )
    logger.info(f"{hello_everybody} переведены в статус 1")
    await bot.send_message(
        user_id,
        f"1. К обновлению готов!\n{hello_everybody.keys()} переведены в статус 1\n\n"
        "2. Останови Бота на сервере:\n"
        "➡️ CTRL+C или CTRL+Z",
    )

    for user in hello_everybody.keys():
        await set_reset_autobuy(user, 1)


@admin_router.callback_query(F.data == "restart")
async def rstart_autobuy(message: Message, bot: Bot):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    if not user_id in all_admins:
        return
    await bot.send_message(user_id, "Колбаса сработала - 👍 Бот запущен !")

    service = RestartUserService(bot)
    await service.restart_all_active_users(notify_admin_id=user_id)


@admin_router.callback_query(F.data == "get_logs")
async def get_logs(message: Message, bot: Bot):
    user_id = message.from_user.id
    if not await AdminChecker().check_user_is_admin(user_id):
        return
    await AdminsMessageService().send_admin_main_logger_file(bot, admin_id=user_id)


@admin_router.message(Command("all"))
async def go_work_command(message: types.Message, bot: Bot, command: CommandObject):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    if not user_id in all_admins:
        return
    today = datetime.today().date()
    active = today - timedelta(days=11)
    all_users = await get_all_id_with_registered_to_status(active)
    arg = command.args
    not_delivered = []
    delivered = []

    if not arg:
        await bot.send_message(
            user_id,
            "Введите команду /all Текст сообщения\nПример: /all Текст сообщения",
        )
        return

    else:
        message_text = arg.strip()
        header = "‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️"
        result_msg = f"{header}\n\n{message_text}\n\nПоддержка 👉 @Infinty_Support"
        for user in all_users:
            try:
                await bot.send_message(user, result_msg)
                delivered.append(user)
            except Exception as e:
                logger.warning(
                    f"Ошибка при отправке сообщения пользователю {user} - {e}"
                )
                not_delivered.append(user)
    if not not_delivered:
        await bot.send_message(
            user_id, f"Сообщение отправлено пользователям - {delivered}"
        )
        return
    else:
        await bot.send_message(
            user_id,
            f"Сообщение отправлено пользователям - {delivered}\n\n Но у пользователей {not_delivered} произошел сбой",
        )


@admin_router.message(Command("m"))
async def go_work_command(message: types.Message, bot: Bot, command: CommandObject):
    user_id = message.from_user.id
    all_admins = await is_admin_checker(user_id)
    if not user_id in all_admins:
        return
    arg = command.args
    if not arg:
        await bot.send_message(
            user_id,
            "Введите команду /m user_id Текст сообщения\nПример: /m 94394949 Текст сообщения",
        )
        return
    info_user_id = command.args.split(" ", 1)
    if len(info_user_id) < 2:
        await bot.send_message(
            user_id,
            "Введите команду /m user_id Текст сообщения\nПример: /m 94394949 Текст сообщения",
        )
        return
    else:
        user_send_message_id = info_user_id[0]
        header = "‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️‼️"
        message_text = (
            f"{header}\n\n{info_user_id[1]} \n\nПоддержка 👉 @Infinty_Support"
        )
        try:
            await bot.send_message(user_send_message_id, message_text)
        except Exception as e:
            error_mes = f"Ошибка при отправке сообщения пользователю {user_send_message_id} - {e}"
            if "chat not found" in str(e):
                error_mes = "Пользователь не найден, проверьте id пользователя и попробуйте еще раз"

            logger.warning(error_mes)
            await bot.send_message(user_id, error_mes)
            return
    await bot.send_message(user_id, "Сообщение доставлено ️️️‼️")
