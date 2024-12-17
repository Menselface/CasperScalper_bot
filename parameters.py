from aiogram import types, Router, F, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from loguru import logger
from pydantic import ValidationError

from config import PAIR_TABLE_MAP
from db import set_autobuy_down_db
from first_reg import check_status_of_registration
from keyboards import params_keyboard, \
    user_autobuy_down_keyboard_off, back_keyboard, yes_no_keyboard, params_choice_symbol, ParamsMyCallbackSymbol
from trading.db_querys.db_symbols_for_trade_methods import get_user_symbol_data, update_user_symbol_data, \
    set_standart_user_params, set_standart_user_params_for_all, get_user_exist_with_symbol, add_user
from utils.additional_methods import format_symbol, safe_format
from utils.only_int import find_only_integer, find_only_integer_int

parameters_router = Router()


class ParametersState(StatesGroup):
    order_limit = State()
    percent_profit = State()
    user_trade_limit = State()
    autobuy_down_percent = State()


@parameters_router.callback_query(StateFilter('*'), F.data == 'cancel_to_parametrs')
async def handle_parameters_choice_symbol(message: types.Message, state: FSMContext, bot: Bot):
    await state.set_state(None)
    user_id = message.from_user.id
    text, status = await check_status_of_registration(message)
    if not status:
        await message.answer(text)
        return
    for symbol in PAIR_TABLE_MAP.keys():
        user_exist = await get_user_exist_with_symbol(user_id, symbol)
        if not user_exist:
            await add_user(user_id, symbol=symbol, start_stop=False)
    await bot.send_message(
        chat_id=user_id,
        text="Выберите торговую пару",
        reply_markup=await params_choice_symbol()
    )


@parameters_router.callback_query(ParamsMyCallbackSymbol.filter())
async def user_choice_symbol_in_params(callback: CallbackQuery, callback_data: ParamsMyCallbackSymbol, bot: Bot,
                                       state: FSMContext):
    user_id = callback.from_user.id
    action = callback_data.action
    symbol = action.split("_")[-1]
    text_area_symbol = format_symbol(symbol)
    await state.update_data(symbol=symbol)
    if action.startswith("set_order_limit_"):
        mes = await callback.message.answer(f"Введите новый размер ордера ({text_area_symbol}):",
                                            reply_markup=await back_keyboard())
        await state.update_data(message_id_callback=mes.message_id)
        await state.set_state(ParametersState.order_limit)
        return
    
    if action.startswith("set_profit_percent_"):
        mes = await callback.message.answer("Введите новый процент прибыли (%):",
                                            reply_markup=await back_keyboard())
        await state.update_data(message_id_callback=mes.message_id)
        await state.set_state(ParametersState.percent_profit)
        return
    
    if action.startswith("limit_of_trading_"):
        if text_area_symbol == "everything":
            mes = await callback.message.answer(f"Введите лимит покупки для всех пар",
                                                reply_markup=await back_keyboard())
            await state.update_data(message_id_callback=mes.message_id)
            await state.set_state(ParametersState.user_trade_limit)
            return
        
        mes = await callback.message.answer(f"Введите лимит покупки для пары {text_area_symbol}",
                                            reply_markup=await back_keyboard())
        await state.update_data(message_id_callback=mes.message_id)
        await state.set_state(ParametersState.user_trade_limit)
        return
    
    if action.startswith("set_autobuy_down_"):
        user_id = callback.from_user.id
        autobuy_status = await get_user_symbol_data(user_id, symbol, 'auto_buy_down_perc')
        if not autobuy_status:
            result = 0
            for pair in PAIR_TABLE_MAP:
                result += await get_user_symbol_data(user_id, pair, 'auto_buy_down_perc')
            if result == 4000:
                mes = await callback.message.answer(
                    "Процент при падении у вас сейчас отключен по всем торговым парам.\nВведите процент для автопокупки при падении и он включится автоматически:",
                    reply_markup=await back_keyboard())
                await state.update_data(message_id_callback=mes.message_id)
                await state.set_state(ParametersState.autobuy_down_percent)
                return
            else:
                mes = await callback.message.answer("Введите процент для автопокупки при падении (%):",
                                                    reply_markup=await user_autobuy_down_keyboard_off())
                await state.update_data(message_id_callback=mes.message_id)
                await state.set_state(ParametersState.autobuy_down_percent)
                return
        
        if autobuy_status != 1000:
            mes = await callback.message.answer("Введите процент для автопокупки при падении (%):",
                                                reply_markup=await user_autobuy_down_keyboard_off())
            await state.update_data(message_id_callback=mes.message_id)
            await state.set_state(ParametersState.autobuy_down_percent)
            return
        else:
            mes = await callback.message.answer(
                "Процент при падении у вас сейчас отключен.\nВведите процент для автопокупки при падении и он включится автоматически:",
                reply_markup=await back_keyboard())
            await state.update_data(message_id_callback=mes.message_id)
            await state.set_state(ParametersState.autobuy_down_percent)
            return
    
    if action.startswith("reset_settings_"):
        mes = await callback.message.answer(f"Сбросить параметры на стандартные для пары {text_area_symbol}?\n"
                                            "Размер ордера - <b>5.0</b> USDT\n"
                                            "Процент прибыли - <b>0.80</b> %\n"
                                            "Процент падения ⬇️ - <b>1 %</b>\n"
                                            "Лимит на покупки ♾️",
                                            reply_markup=await yes_no_keyboard())
        await state.update_data(message_id_callback=mes.message_id)
        return
    if action == "all_pairs":
        mes = await bot.send_message(user_id,
                                     f"Настройки торговли для всех пар:",
                                     reply_markup=await params_keyboard(user_id, symbol, for_everything=True))
        await state.update_data(message_id=mes.message_id)
        return
    mes = await bot.send_message(user_id,
                                 f"Настройки торговли {text_area_symbol}:",
                                 reply_markup=await params_keyboard(user_id, symbol))
    await state.update_data(message_id=mes.message_id)


@parameters_router.callback_query(F.data == 'yes_callback')
async def set_autobuy_down(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id
    mes = await callback_query.message.answer("Параметры сброшены на стандартные ✅\n")
    data = await state.get_data()
    message_id_callback = data.get("message_id_callback")
    message_id = data.get("message_id")
    symbol = data.get("symbol")
    if symbol == "everything":
        await set_standart_user_params_for_all(user_id)
        await delete_message(user_id, message_id_callback, bot)
        return
    await set_standart_user_params(user_id, symbol)
    text_area_symbol = format_symbol(symbol)
    
    await delete_message(user_id, message_id_callback, bot)
    mes = await bot.edit_message_text(
        chat_id=user_id,
        text=f'Настройки торговли {text_area_symbol}:',
        message_id=message_id,
        reply_markup=await params_keyboard(user_id, symbol)
    )
    await state.update_data(message_id=mes.message_id)
    logger.info(f"Пользователь {user_id}: - Параметры сброшены на стандартные ✅")
    return


@parameters_router.callback_query(StateFilter(ParametersState.autobuy_down_percent), F.data == 'autobuy_off')
async def autobuy_off(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    symbol = data.get("symbol")
    text_area_symbol = format_symbol(symbol)
    if text_area_symbol == "everything":
        text_area_symbol = "всех торговых пар"
        user_id = callback_query.from_user.id
        for pair in PAIR_TABLE_MAP.keys():
            await update_user_symbol_data(user_id, pair, auto_buy_down_perc=1000)
        await state.set_state(None)
        mes = await callback_query.message.answer(f"Процент покупки для {text_area_symbol} при падении отключен ✅\n")
        return
    await state.set_state(None)
    user_id = callback_query.from_user.id
    await update_user_symbol_data(user_id, symbol, auto_buy_down_perc=1000)
    mes = await callback_query.message.answer(f"Процент покупки для {text_area_symbol} при падении отключен ✅\n")
    await delete_message(user_id, message_id_callback, bot)
    
    logger.info(f"Пользователь {user_id}: - Процент покупки при падении отключен ✅")


@parameters_router.message(StateFilter(ParametersState.order_limit))
async def process_order_limit(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_new_limit = await find_only_integer_int(message.text)
    data = await state.get_data()
    symbol = data.get("symbol")
    value = await get_user_symbol_data(user_id, symbol, 'order_limit_by')
    user_old_parametr = round(value, 2) if value is not None else ""
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    if not user_new_limit or user_new_limit < 5:
        await message.answer(
            "Сумма разрешённая биржей не может быть менее <b>5$</b>.\nВведите размер ордера целым числом:")
        return
    
    if symbol == "everything":
        text_area_symbol = "Для всех торговых пар"
        symbols_to_update = list(PAIR_TABLE_MAP.keys())
    else:
        text_area_symbol = format_symbol(symbol)
        symbols_to_update = [symbol]
    
    for sym in symbols_to_update:
        await update_user_symbol_data(user_id, sym, order_limit_by=round(user_new_limit))
    
    await message.delete()
    await message.answer(
        f"Размер ордера {text_area_symbol} изменен:\n {user_old_parametr} → {round(float(message.text), 2)}"
    )
    
    await state.set_state(None)
    await delete_message(user_id, message_id_callback, bot)
    if symbol != "everything":
        mes = await bot.edit_message_text(
            chat_id=user_id,
            text=f'Настройки торговли {text_area_symbol}:',
            message_id=message_id,
            reply_markup=await params_keyboard(user_id, symbol)
        )
        await state.update_data(message_id=mes.message_id)
    logger.info(f"Пользователь {user_id}: Размер ордера изменен на {user_new_limit}")


@parameters_router.message(StateFilter(ParametersState.percent_profit))
async def process_percent_profit(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_new_limit = await find_only_integer(message.text)
    data = await state.get_data()
    symbol = data.get("symbol")
    value = await get_user_symbol_data(user_id, symbol, 'percent_profit')
    user_old_parametr = round(value, 2) if value is not None else ""
    data = await state.get_data()
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    if not (0.3 <= user_new_limit < 100.0):
        await message.answer('Пожалуйста введите значение только цифрами от 0.3 до 99%')
        return
    
    if symbol == "everything":
        text_area_symbol = "Для всех торговых пар"
        symbols_to_update = list(PAIR_TABLE_MAP.keys())
    else:
        text_area_symbol = format_symbol(symbol)
        symbols_to_update = [symbol]
    
    for sym in symbols_to_update:
        await update_user_symbol_data(user_id, sym, percent_profit=round(user_new_limit, 2))
    
    await message.delete()
    user_old_parametr = safe_format(user_old_parametr, 2)
    await message.answer(
        f"Процент прибыли для {text_area_symbol} (%) изменен:\n <b>{user_old_parametr or ''} → {round(float(message.text), 2)}</b> ")
    await state.set_state(None)
    await delete_message(user_id, message_id_callback, bot)
    if symbol != "everything":
        mes = await bot.edit_message_text(
            chat_id=user_id,
            text=f'Настройки торговли {text_area_symbol}:',
            message_id=message_id,
            reply_markup=await params_keyboard(user_id, symbol)
        )
        await state.update_data(message_id=mes.message_id)


@parameters_router.message(StateFilter(ParametersState.user_trade_limit))
async def process_user_trade_limit(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_new_limit = await find_only_integer(message.text)
    user_new_limit = int(user_new_limit)
    data = await state.get_data()
    symbol = data.get("symbol")
    user_old_parametr = await get_user_symbol_data(user_id, symbol, 'trade_limit') or ""
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    if not user_new_limit:
        await message.answer('Пожалуйста введите значение только <b>целыми</b> числами.')
    
    if symbol == "everything":
        text_area_symbol = "Для всех торговых пар"
        symbols_to_update = list(PAIR_TABLE_MAP.keys())
    else:
        text_area_symbol = format_symbol(symbol)
        symbols_to_update = [symbol]
    
    for sym in symbols_to_update:
        await update_user_symbol_data(user_id, sym, trade_limit=round(user_new_limit))
    
    await message.delete()
    
    await message.answer(
        f"Лимит покупки для {text_area_symbol} изменен:\n <b>{user_old_parametr} → {message.text}</b> ")
    await state.set_state(None)
    await delete_message(user_id, message_id_callback, bot)
    if symbol != "everything":
        mes = await bot.edit_message_text(
            chat_id=user_id,
            text=f'Настройки торговли {text_area_symbol}:',
            message_id=message_id,
            reply_markup=await params_keyboard(user_id, symbol)
        )
        await state.update_data(message_id=mes.message_id)


@parameters_router.message(StateFilter(ParametersState.autobuy_down_percent))
async def process_autobuy_down(message: types.Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    user_new_limit = await find_only_integer(message.text)
    user_new_limit = float(user_new_limit)
    data = await state.get_data()
    symbol = data.get("symbol")
    message_id = data.get("message_id")
    message_id_callback = data.get("message_id_callback")
    if not user_new_limit >= 0.3:
        await message.answer('Минимальный процент падения может составлять 0.3 %, пожалуйста введите корректное число:')
        return
    if symbol == "everything":
        text_area_symbol = "Для всех торговых пар"
        symbols_to_update = list(PAIR_TABLE_MAP.keys())
        await message.answer(
            f"Процент падения для {text_area_symbol} (%) изменен для всех пар → {safe_format(float(message.text), 2)}.")
    else:
        user_old_parametr = await get_user_symbol_data(user_id, symbol, 'auto_buy_down_perc')
        text_area_symbol = format_symbol(symbol)
        symbols_to_update = [symbol]
        await message.answer(
            f"Процент падения для {text_area_symbol} (%) изменен:\n <b>{safe_format(user_old_parametr, 2) if user_old_parametr != 1000 else '♾'} → {round(float(message.text), 2)}</b> ")
    
    for sym in symbols_to_update:
        await update_user_symbol_data(user_id, sym, auto_buy_down_perc=round(user_new_limit, 2))
    
    await message.delete()
    
    logger.info(f"Пользователь {user_id}: Процент падения (%) изменен: {user_new_limit}")
    
    await delete_message(user_id, message_id_callback, bot)
    await state.set_state(None)
    if symbol != "everything":
        mes = await bot.edit_message_text(
            chat_id=user_id,
            text=f'Настройки торговли {text_area_symbol}:',
            message_id=message_id,
            reply_markup=await params_keyboard(user_id, symbol)
        )
        await state.update_data(message_id=mes.message_id)


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
