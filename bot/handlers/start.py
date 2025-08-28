import datetime
import json

from aiogram import Router, Bot, F, types
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.utils.serialization import deserialize_telegram_object_to_python

from bot.keyboards.keyboards import trial_keyboard
from infrastructure.db_pack.db import (
    add_user,
    user_exist,
    get_access_key,
    get_timestamp_of_registration,
    user_get_any,
    user_update,
    set_access_key,
    set_secret_key,
    get_timestamp_end_registration,
)
from infrastructure.db_pack.repositories.users import UpdateUserRepo
from services.admins.admins_message import AdminsMessageService
from utils.decorators import send_message_safe_call
from utils.inactive_users import check_inactive_user
from utils.user_api_keys_checker import validation_user_keys

start_router = Router()


class RegistrationStates(StatesGroup):
    access_key_state = State()
    secret_key_state = State()


@start_router.message(Command("start"))
@send_message_safe_call(default_return=[])
async def handle_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    username = "Нет"
    first_name = "Нет"
    last_name = "Нет"
    date_time = datetime.datetime.now()
    date_time = date_time.replace(second=0, microsecond=0)
    specific_date = datetime.datetime(1990, 1, 1, 23, 59)
    text, status_of_expired = await check_status_of_registration(message)
    access_key = await get_access_key(user_id)
    message_json = json.dumps(deserialize_telegram_object_to_python(message))
    await UpdateUserRepo().user_first_message_obj(user_id, message_json)

    if message.from_user.first_name:
        first_name = message.from_user.first_name
    if message.from_user.last_name:
        last_name = message.from_user.last_name
    if message.from_user.username:
        username = f"@{message.from_user.username}"

    lang = message.from_user.language_code if message.from_user.language_code else "en"

    if not await user_exist(user_id):

        await add_user(
            user_id, first_name, last_name, username, date_time, specific_date, lang)
        await check_inactive_user(user_id)
        admin_message = (
            f"Новый пользователь зарегистрировался!"
            f"\n\n{date_time.strftime('%d.%m.%Y %H:%M')}\nID: {user_id}\n"
            f"Имя: {first_name}\n"
            f"Имя пользователя: {username}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=trial_keyboard())
        await AdminsMessageService().send_to_all_admins_message_text(admin_message, bot)
    else:
        timestamp = await get_timestamp_of_registration(user_id)
        user_message = f"Привет, {first_name}.\nВы уже зарегистрированы {timestamp}"
        if not access_key:
            await message.answer(
                "Для начала регистрации введи /registration", parse_mode="HTML")
            return

        await bot.send_message(user_id, user_message, parse_mode="HTML")
        await message.answer(text, parse_mode="HTML")
    await UpdateUserRepo().user_first_message_obj(user_id, message_json)


@start_router.message(StateFilter(None), Command("registration"))
async def handle_registration(message: Message, state: FSMContext):
    access_key = await get_access_key(message.from_user.id)
    text, _ = await check_status_of_registration(message)
    if access_key:
        await message.answer(text, parse_mode="HTML")
        return
    text, status_of_expired = await check_status_of_registration(message)
    if not status_of_expired:
        await message.answer(
            "Добро пожаловать. Следуйте инструкции ниже:\n\n",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

        await message.answer(
            "<b>Введи Access Key (начинается на mx…):</b>", parse_mode="HTML"
        )

        await state.set_state(RegistrationStates.access_key_state)
        return
    else:
        await message.answer(text, parse_mode="HTML")


@start_router.callback_query(F.data.startswith("set_trial_promo"))
async def set_trial_for_user(
    callback_query: types.CallbackQuery, state: FSMContext, bot: Bot
):
    user_id = callback_query.from_user.id
    user_first_trial = await user_get_any(user_id, trial_promo="trial_promo")
    today = datetime.datetime.now()
    if user_first_trial:
        await bot.send_message(
            chat_id=user_id, text="Ваш пробный период уже был активирован ранее\n\n"
        )
        return
    today = datetime.datetime.now()
    trial_period = (today + datetime.timedelta(days=7)).replace(
        hour=23, minute=59, second=0, microsecond=0
    )
    await user_update(user_id, registered_to=trial_period)
    await callback_query.answer("Пробный период активирован! 🎉", show_alert=True)
    await user_update(user_id, trial_promo=True)
    await handle_registration(callback_query.message, state)


@start_router.message(StateFilter(RegistrationStates.access_key_state))
async def handle_access_key(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await set_access_key(user_id, message.text.strip())
    await state.clear()
    await message.answer("<b>Теперь введите ваш Secret Key:</b>")
    await state.set_state(RegistrationStates.secret_key_state)


@start_router.message(StateFilter(RegistrationStates.secret_key_state))
async def handle_secret_key(message: Message, state: FSMContext, bot: Bot):
    text, _ = await check_status_of_registration(message)
    user_id = message.from_user.id
    username = message.from_user.username or user_id
    await set_secret_key(user_id, message.text.strip())
    await state.clear()
    check_api_keys = await validation_user_keys(user_id)
    if not check_api_keys:
        admin_message = (
            f"Пользователь @{username} ввел некоректные ключи при регистрации"
        )
        await bot.send_message(user_id, "Ошибка в апи ключах, сообщите в поддержку @AlisaStrange.")
        await AdminsMessageService().send_to_all_admins_message_text(admin_message, bot)
    else:
        await message.answer(text, parse_mode="HTML")


async def check_status_of_registration(message: Message) -> tuple[str, bool]:
    """Я добавил эту функцию для проверки статуса во всех остальных хендлерах.
    Если возвращается False, пользователю будут доступны только 'Старт' и 'Регистрация'.
    """

    user_id = message.from_user.id
    expired_timestamp = await get_timestamp_end_registration(user_id)
    timestamp = await get_timestamp_of_registration(user_id)
    date_time = datetime.datetime.now()
    date_time = date_time.replace(second=0, microsecond=0)
    user_message2 = (f"Привет, {message.from_user.first_name}.",)

    if not expired_timestamp:
        return f"<b>KasperScalper</b>\n\n{user_message2}", False
    elif expired_timestamp < date_time:
        return (
            f"Ваша регистрация закончилась – Зарегистрирован до: {expired_timestamp}\nСвяжитесь с поддержкой ➡️ @AlisaStrange\n\n<b>После ПОДТВЕРЖДЕНИЯ оплаты, жми ➡️  /registration  ⬅️</b>\n",
            False,
        )
    else:
        return (
            f"<b>Регистрация до – {expired_timestamp}</b>\n\nПополните свой спотовый счёт на Mexc.com USDT для торговли.\n\nНачинайте, торговать:\nМеню - /parameters и СТАРТ - /trade\n\nЕсть вопросы? Пиши в поддержку: @AlisaStrange",
            True,
        )
