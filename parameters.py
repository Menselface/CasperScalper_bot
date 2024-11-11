import traceback

from aiogram import types, Router, F, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from pydantic import ValidationError
from loguru import logger

from db import get_user_order_limit, get_info_percent_profit, get_await_time, get_info_percent_auto_buy, \
    set_percent_profiit, set_autobuy_up_db, set_autobuy_down_db, set_user_limit_order, set_standart_user_params, \
    set_commission_percent, get_info_commission_percent, get_secret_key, get_access_key
from first_reg import check_status_of_registration
from utils.commission_cheker import check_user_own_commission
from utils.only_int import find_only_integer, find_only_integer_int
from keyboards import params_keyboard, \
    user_autobuy_down_keyboard_off, back_keyboard, yes_no_keyboard, user_commission_choices, commission_to_url

parameters_router = Router()


class ParametersState(StatesGroup):
    order_limit = State()
    percent_profit = State()
    autobuy_up_sec = State()
    autobuy_down_percent = State()


async def handle_parameters(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    text, status = await check_status_of_registration(message)
    if not status:
        await message.answer(text)
        return
    
    user_order_limit = await get_user_order_limit(user_id)
    percent_profit = await get_info_percent_profit(user_id)
    autobuy_up_sec = await get_await_time(user_id)
    autobuy_down_percent = await get_info_percent_auto_buy(user_id)
    commission_percent = await get_info_commission_percent(user_id)
    
    keyboard = await params_keyboard(user_order_limit, percent_profit, autobuy_up_sec, autobuy_down_percent,
                                     taker=commission_percent)
    
    sent_message = await message.answer("Настройки торговли:", reply_markup=keyboard)
    await state.update_data(message_id=sent_message.message_id)


@parameters_router.callback_query(F.data == 'set_order_limit')
async def set_order_limit(callback_query: types.CallbackQuery, state: FSMContext):
    mes = await callback_query.message.answer("Введите новый размер ордера (USDT):", reply_markup=await back_keyboard())
    await state.update_data(message_id_callback=mes.message_id)
    await state.set_state(ParametersState.order_limit)


@parameters_router.callback_query(F.data == 'set_profit_percent')
async def set_profit_percent(callback_query: types.CallbackQuery, state: FSMContext):
    mes = await callback_query.message.answer("Введите новый процент прибыли (%):", reply_markup=await back_keyboard())
    await state.update_data(message_id_callback=mes.message_id)
    await state.set_state(ParametersState.percent_profit)


@parameters_router.callback_query(F.data == 'set_autobuy_up')
async def set_autobuy_up(callback_query: types.CallbackQuery, state: FSMContext):
    mes = await callback_query.message.answer("Введите время для автопокупки при росте (сек):",
                                              reply_markup=await back_keyboard())
    await state.update_data(message_id_callback=mes.message_id)
    await state.set_state(ParametersState.autobuy_up_sec)


@parameters_router.callback_query(F.data == 'set_autobuy_down')
async def set_autobuy_down(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    autobuy_status = await get_info_percent_auto_buy(user_id)
    if autobuy_status != 1000:
        mes = await callback_query.message.answer("Введите процент для автопокупки при падении (%):",
                                                  reply_markup=await user_autobuy_down_keyboard_off())
        await state.update_data(message_id_callback=mes.message_id)
        await state.set_state(ParametersState.autobuy_down_percent)
    else:
        mes = await callback_query.message.answer(
            "Процент при падении у вас сейчас отключен.\nВведите процент для автопокупки при падении и он включится автоматически:",
            reply_markup=await back_keyboard())
        await state.update_data(message_id_callback=mes.message_id)
        await state.set_state(ParametersState.autobuy_down_percent)


@parameters_router.callback_query(F.data == 'reset_settings')
async def set_autobuy_down(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    mes = await callback_query.message.answer("Сбросить параметры на стандартные?\n"
                                              "Размер ордера - <b>30.0</b> USDT\n"
                                              "Процент прибыли - <b>0.30</b> %\n"
                                              "Интервал покупки - <b>30.0</b> сек\n"
                                              "Процент падения ⬇️ - <b>1 %</b>\n"
                                              "Комиссия - Mейкер: 0.00% | Tейкер: 0.02%",
                                              reply_markup=await yes_no_keyboard())
    await state.update_data(message_id_callback=mes.message_id)


@parameters_router.callback_query(F.data == 'yes_callback')
async def set_autobuy_down(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id
    await set_standart_user_params(user_id)
    mes = await callback_query.message.answer("Параметры сброшены на стандартные ✅\n")
    data = await state.get_data()
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    await delete_message(user_id, message_id_callback, bot)
    await delete_message(user_id, message_id, bot)
    logger.info(f"Пользователь {user_id}: - Параметры сброшены на стандартные ✅")


@parameters_router.callback_query(StateFilter(ParametersState.autobuy_down_percent), F.data == 'autobuy_off')
async def set_autobuy_down(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    await state.clear()
    user_id = callback_query.from_user.id
    await set_autobuy_down_db(user_id, 1000)
    mes = await callback_query.message.answer("Процент покупки при падении отключен ✅\n")
    await delete_message(user_id, message_id_callback, bot)
    await delete_message(user_id, message_id, bot)
    logger.info(f"Пользователь {user_id}: - Процент покупки при падении отключен ✅")


@parameters_router.callback_query(StateFilter('*'), F.data == 'cancel_to_parametrs')
async def set_autobuy_down(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    await delete_message(user_id, message_id_callback, bot)
    await delete_message(user_id, message_id, bot)
    await state.clear()
    user_order_limit = await get_user_order_limit(user_id)
    percent_profit = await get_info_percent_profit(user_id)
    autobuy_up_sec = await get_await_time(user_id)
    autobuy_down_percent = await get_info_percent_auto_buy(user_id)
    commission_percent = await get_info_commission_percent(user_id)
    
    keyboard = await params_keyboard(user_order_limit, percent_profit, autobuy_up_sec, autobuy_down_percent,
                                     taker=commission_percent)
    
    sent_message = await bot.send_message(user_id, "Настройки торговли:", reply_markup=keyboard)
    await state.update_data(message_id=sent_message.message_id)


@parameters_router.callback_query(F.data == 'set_user_commission')
async def get_user_commission_keybs(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    await delete_message(user_id, message_id_callback, bot)
    await delete_message(user_id, message_id, bot)
    
    sent_message = await bot.send_message(user_id, "<b>Выберите комиссию:</b>",
                                          reply_markup=await user_commission_choices())
    await state.update_data(message_id=sent_message.message_id)


@parameters_router.callback_query(F.data == 'user_check_commission')
async def get_user_commission_keybs(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    await delete_message(user_id, message_id_callback, bot)
    await delete_message(user_id, message_id, bot)
    
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    result = check_user_own_commission(user_api_keys, user_secret_key)
    maker = result['makerCommission']
    taker = result['takerCommission']
    sent_message = await bot.send_message(user_id,
                                          f"<i>На вашем аккаунте установлена такая комиссия биржи:</i>\n\n<b>Mейкер: {maker}% | Tейкер: {taker}%</b>",
                                          reply_markup=commission_to_url())
    await state.update_data(message_id=sent_message.message_id)


@parameters_router.callback_query(F.data.startswith('set_user_commission_'))
async def set_user_commission(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id
    data = await state.get_data()
    
    callback_data = callback_query.data
    
    if callback_data == 'set_user_commission_1':
        await set_commission_percent(user_id, 0.010)
        await callback_query.answer("Вы выбрали Mейкер: 0.00% | Tейкер: 0.010%")
    elif callback_data == 'set_user_commission_2':
        await set_commission_percent(user_id, 0.016)
        await callback_query.answer("Вы выбрали Mейкер: 0.00% | Tейкер: 0.016%")
    elif callback_data == 'set_user_commission_3':
        await set_commission_percent(user_id, 0.020)
        await callback_query.answer("Вы выбрали Mейкер: 0.00% | Tейкер: 0.020%")
    elif callback_data == 'set_user_commission_4':
        user_api_keys = await get_access_key(user_id)
        user_secret_key = await get_secret_key(user_id)
        result = check_user_own_commission(user_api_keys, user_secret_key)
        maker = result['makerCommission']
        taker = result['takerCommission']
        await set_commission_percent(user_id, taker)
        await callback_query.answer(f"Вы выбрали Mейкер: {maker}% | Tейкер: {taker}%")
    
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    
    await delete_message(user_id, message_id_callback, bot)


@parameters_router.message(StateFilter(ParametersState.order_limit))
async def process_order_limit(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_old_parametr = round(await get_user_order_limit(user_id), 2)
    user_new_limit = await find_only_integer_int(message.text)
    if user_new_limit >= 5:
        data = await state.get_data()
        message_id = data.get("message_id")
        message_id_callback = data.get("message_id_callback")
        await set_user_limit_order(user_id, round(user_new_limit))
        await message.answer(f"Размер ордера USDT изменен:\n {user_old_parametr} → {round(float(message.text), 2)}")
        await state.clear()
        await delete_message(user_id, message_id, bot)
        await delete_message(user_id, message_id_callback, bot)
        logger.info(f"Пользователь {user_id}: Размер ордера USDT изменен: {user_new_limit}")
        
        return
    if not user_new_limit:
        await message.answer('Пожалуйста введите значение только целым числом от<b> 5$</b>')
        
    else:
        await message.answer("Сумма разрешенная биржей не может быть менее<b> 5$</b>.\nВведите размер ордера:")

# изменил 245 строку - было <99  я поставил <100 "if 0.1 <= user_new_limit < 100.0:"
@parameters_router.message(StateFilter(ParametersState.percent_profit))
async def process_percent_profit(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_old_parametr = round(await get_info_percent_profit(user_id), 2)
    user_new_limit = await find_only_integer(message.text)
    if 0.3 <= user_new_limit < 100.0:
        data = await state.get_data()
        message_id = data.get("message_id")
        message_id_callback = data.get("message_id_callback")
        await set_percent_profiit(user_id, round(user_new_limit, 2))
        await message.answer(
            f"Процент прибыли (%) изменен:\n <b>{user_old_parametr} → {round(float(message.text), 2)}</b> ")
        await state.clear()
        await delete_message(user_id, message_id, bot)
        await delete_message(user_id, message_id_callback, bot)
        logger.info(f"Пользователь {user_id}: Процент прибыли (%) изменен: {user_new_limit}")
        
        return
    if not user_new_limit:
        await message.answer('Пожалуйста введите значение только цифрами от 0.3 до 99%')
    else:
        await message.answer('Пожалуйста введите от<b> 0.3 до 99% </b>')


@parameters_router.message(StateFilter(ParametersState.autobuy_up_sec))
async def process_autobuy_up(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_old_parametr = await get_await_time(user_id)
    user_new_limit = await find_only_integer(message.text)
    user_new_limit = int(user_new_limit)
    if user_new_limit:
        data = await state.get_data()
        message_id = data.get("message_id")
        message_id_callback = data.get("message_id_callback")
        await set_autobuy_up_db(user_id, round(user_new_limit, 2))
        await message.answer(f"Интервал автопокупки (сек) изменен:\n <b>{user_old_parametr} → {message.text}</b> ")
        await state.clear()
        await delete_message(user_id, message_id, bot)
        await delete_message(user_id, message_id_callback, bot)
        logger.info(f"Пользователь {user_id}: Интервал автопокупки (сек) изменен: {user_new_limit}")
        return
    else:
        await message.answer('Пожалуйста введите значение только <b>целыми</b> числами в секундах')


@parameters_router.message(StateFilter(ParametersState.autobuy_down_percent))
async def process_autobuy_down(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_old_parametr = await get_info_percent_auto_buy(user_id)
    if isinstance(user_old_parametr, float):
        user_old_parametr = round(user_old_parametr, 2)
    user_new_limit = await find_only_integer(message.text)
    user_new_limit = float(user_new_limit)
    if user_new_limit >= 0.3:
        data = await state.get_data()
        message_id = data.get("message_id")
        message_id_callback = data.get("message_id_callback")
        await set_autobuy_down_db(user_id, round(user_new_limit, 2))
        await message.answer(
            f"Процент падения (%) изменен:\n <b>{user_old_parametr if user_old_parametr != 1000 else '♾'} → {round(float(message.text), 2)}</b> ")
        logger.info(f"Пользователь {user_id}: Процент падения (%) изменен: {user_new_limit}")
        await delete_message(user_id, message_id, bot)
        await delete_message(user_id, message_id_callback, bot)
        await state.clear()
    else:
        await message.answer('Минимальный процент падения может составлять 0.3 %, пожалуйста введите корректное число:')


async def delete_message(user_id, message_id, bot: Bot):
    if isinstance(message_id, int):
        try:
            await bot.delete_message(user_id, message_id)
        except ValidationError as ve:
            pass
        except TelegramAPIError as tae:
            pass
        except Exception as e:
            pass
    else:
        pass
