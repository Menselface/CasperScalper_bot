from datetime import datetime

from aiogram import Router, Bot, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.serialization import deserialize_telegram_object_to_python

from config import ADMIN_ID
from db import *
from keyboards import trial_keyboard
from utils.user_api_keys_checker import validation_user_keys

registration_states_router = Router()


class RegistrationStates(StatesGroup):
    access_key_state = State()
    secret_key_state = State()


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
    
    if message.from_user.first_name:
        first_name = message.from_user.first_name
    if message.from_user.last_name:
        last_name = message.from_user.last_name
    if message.from_user.username:
        username = f'@{message.from_user.username}'
    
    if not await user_exist(user_id):
        await add_user(user_id, first_name, last_name, username, date_time, specific_date)
        admin_message = (
            f"Новый пользователь зарегистрировался!"
            f"\n\n{date_time.strftime('%d.%m.%Y %H:%M')}\nID: {user_id}\n"
            f"Имя: {first_name}\n"
            f"Имя пользователя: {username}"
        )
        await message.answer(text, parse_mode='HTML', reply_markup=trial_keyboard())
        await bot.send_message(ADMIN_ID, admin_message, parse_mode='HTML')
        await bot.send_message(ADMIN_ID2, admin_message, parse_mode='HTML')
        await set_first_message(user_id, message_json)
    else:
        timestamp = await get_timestamp_of_registration(user_id)
        user_message = f"Привет, {first_name}.\nВы уже зарегистрированы {timestamp}"
        if not access_key:
            await message.answer("Для начала регистрации введи /registration", parse_mode='HTML')
            return
        
        await bot.send_message(user_id, user_message, parse_mode='HTML')
        await message.answer(text, parse_mode='HTML')


async def handle_registration(message: Message, state: FSMContext):
    access_key = await get_access_key(message.from_user.id)
    text, _ = await check_status_of_registration(message)
    if access_key:
        await message.answer(text, parse_mode='HTML')
        return
    text, status_of_expired = await check_status_of_registration(message)
    if not status_of_expired:
        await message.answer(
            "Добро пожаловать. Следуйте инструкции ниже:\n"
            "Сгенерируйте на бирже MEXC.COM в своем личном кабинете API ключи ",
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        await message.answer(
            "<b>Введи Access Key (начинается на mx…):</b>",
            parse_mode='HTML'
        )
        
        await state.set_state(RegistrationStates.access_key_state)
        return
    else:
        await message.answer(text, parse_mode='HTML')


@registration_states_router.callback_query(F.data.startswith('set_trial_promo'))
async def set_trial_for_user(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id
    user_first_trial = await user_get_any(user_id, trial_promo="trial_promo")
    today = datetime.datetime.now()
    if user_first_trial:
        await bot.send_message(
            chat_id=user_id,
            text="Ваш пробный период уже был активирован ранее\n\n"
        )
        return
    today = datetime.datetime.now()
    trial_period = (today + timedelta(days=7)).replace(hour=23, minute=59, second=0, microsecond=0)
    await user_update(user_id, registered_to=trial_period)
    await callback_query.answer("Пробный период активирован! 🎉", show_alert=True)
    await user_update(user_id, trial_promo=True)
    await handle_registration(callback_query.message, state)


@registration_states_router.message(StateFilter(RegistrationStates.access_key_state))
async def handle_access_key(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await set_access_key(user_id, message.text.strip())
    await state.clear()
    await message.answer("<b>Введи Secret Key:</b>", parse_mode='HTML')
    await state.set_state(RegistrationStates.secret_key_state)


@registration_states_router.message(StateFilter(RegistrationStates.secret_key_state))
async def handle_secret_key(message: Message, state: FSMContext, bot: Bot):
    text, _ = await check_status_of_registration(message)
    user_id = message.from_user.id
    username = message.from_user.username or user_id
    await set_secret_key(user_id, message.text.strip())
    await state.clear()
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    check_api_keys = await validation_user_keys(user_api_keys, user_secret_key)
    if not check_api_keys:
        admin_message = f"Пользователь @{username} ввел некоректные ключи при регистрации"
        await bot.send_message(user_id, f'Ошибка в апи ключах, сообщите в поддержку @AlisaStrange.')
        await bot.send_message(ADMIN_ID, admin_message, parse_mode='HTML')
    else:
        await message.answer(text, parse_mode='HTML')


async def check_status_of_registration(message: Message) -> tuple[str, bool]:
    """Я добавил эту функцию для проверки статуса во всех остальных хендлерах.
        Если возвращается False, пользователю будут доступны только 'Старт' и 'Регистрация'.
    """
    
    user_id = message.from_user.id
    expired_timestamp = await get_timestamp_end_registration(user_id)
    timestamp = await get_timestamp_of_registration(user_id)
    date_time = datetime.datetime.now()
    date_time = date_time.replace(second=0, microsecond=0)
    user_message2 = (
        f"Привет, {message.from_user.first_name}.\n\n"
        f"<b>Полная информация по боту:</b>\n"
        f"«Я осознаю все риски торговли криптовалютой, принимаю их на себя и понимаю, что могу стать холдером криптовалюты»\n"
        f"Активируя тестовый период, я подтверждаю своё согласие и готов торговать с помощью Бота\n"
        f"⬇️⬇️⬇️\n\n"
    )
    
    if not expired_timestamp:
        return f"<b>Infinity Bot Pro</b>\n\n{user_message2}", False
    elif expired_timestamp < date_time:
        return f"Ваша регистрация закончилась – Зарегистрирован до: {expired_timestamp}\nСвяжитесь с поддержкой ➡️ @AlisaStrange\n\n<b>После ПОДТВЕРЖДЕНИЯ оплаты, жми ➡️  /registration  ⬅️</b>\n", False
    else:
        return f"Регистрация до – {expired_timestamp}\nПополните свой спотовый счёт на Mexc.com USDT для торговли.\n\nНачинайте, торговать – жми\nМеню - /parameters и СТАРТ - /trade", True