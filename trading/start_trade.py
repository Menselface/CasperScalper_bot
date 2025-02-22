import asyncio

from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from db import get_first_message, get_all_open_sell_orders_autobuy, set_reset_autobuy, \
    get_all_open_sell_orders_autobuy_from_any_table
from keyboards import StartTrade
from trading.db_querys.db_for_btc_table import get_all_open_sell_orders_autobuy_btc
from trading.db_querys.db_symbols_for_trade_methods import get_symbols_for_keyboard, update_user_symbol_data
from trading.sesison_manager_start_stop import user_start_stop
from trading.trading_btc import btc_usdc_trader
from trading.trading_dot_usdt import dot_trader
from trading.trading_kas import kaspa_trader
from trading.trading_pyth import pyth_trader
from trading.trading_sui import sui_trader
from trading.trading_tao import tao_trader
from utils.additional_methods import process_order_result, format_symbol

user_start_trade = Router()


@user_start_trade.callback_query(StartTrade.filter())
async def user_set_up_callbacks(callback: CallbackQuery, callback_data: StartTrade, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id
    action = callback_data.action
    user_data = await user_start_stop.get_session_data(user_id)
    
    btc_status = next((currency.get("BTCUSDC") for currency in user_data if "BTCUSDC" in currency), False)
    kaspa_status = next((currency.get("KASUSDT") for currency in user_data if "KASUSDT" in currency), False)
    sui_status = next((currency.get("SUIUSDT") for currency in user_data if "SUIUSDT" in currency), False)
    pyth_status = next((currency.get("PYTHUSDT") for currency in user_data if "PYTHUSDT" in currency), False)
    dot_status = next((currency.get("DOTUSDT") for currency in user_data if "DOTUSDT" in currency), False)
    tao_status = next((currency.get("TAOUSDT") for currency in user_data if "TAOUSDT" in currency), False)
    
    btc = await get_symbols_for_keyboard(user_id, "BTCUSDC")
    kaspa = await get_symbols_for_keyboard(user_id, "KASUSDT")
    sui = await get_symbols_for_keyboard(user_id, "SUIUSDT")
    pyth = await get_symbols_for_keyboard(user_id, "PYTHUSDT")
    dot = await get_symbols_for_keyboard(user_id, "DOTUSDT")
    tao = await get_symbols_for_keyboard(user_id, "TAOUSDT")
    
    text = await generate_status_text(user_id)
    tasks = []
    res = await get_first_message(user_id)
    result_text = f"{text}\nЧтобы включить или выключить торговлю монетой, зайдите в Меню - «Управление торговлей»  - /trade"
    if action == "start_trade":
        if btc_status and not btc:
            task = asyncio.create_task(btc_usdc_trader(res, bot))
            await update_user_symbol_data(user_id, "BTCUSDC", start_stop=True)
            tasks.append(task)
        elif not btc_status and btc:
            await update_user_symbol_data(user_id, "BTCUSDC", start_stop=False)
        
        if kaspa_status and not kaspa:
            task = asyncio.create_task(kaspa_trader(res, bot))
            await update_user_symbol_data(user_id, "KASUSDT", start_stop=True)
            tasks.append(task)
        elif not kaspa_status and kaspa:
            await update_user_symbol_data(user_id, "KASUSDT", start_stop=False)
        
        if sui_status and not sui:
            task = asyncio.create_task(sui_trader(res, bot))
            await update_user_symbol_data(user_id, "SUIUSDT", start_stop=True)
            tasks.append(task)
        elif not sui_status and sui:
            await update_user_symbol_data(user_id, "SUIUSDT", start_stop=False)
        
        if pyth_status and not pyth:
            task = asyncio.create_task(pyth_trader(res, bot))
            await update_user_symbol_data(user_id, "PYTHUSDT", start_stop=True)
            tasks.append(task)
        elif not pyth_status and pyth:
            await update_user_symbol_data(user_id, "PYTHUSDT", start_stop=False)
        
        if dot_status and not dot:
            task = asyncio.create_task(dot_trader(res, bot))
            await update_user_symbol_data(user_id, "DOTUSDT", start_stop=True)
            tasks.append(task)
        elif not dot_status and dot:
            await update_user_symbol_data(user_id, "DOTUSDT", start_stop=False)
        
        if tao_status and not tao:
            task = asyncio.create_task(tao_trader(res, bot))
            await update_user_symbol_data(user_id, "TAOUSDT", start_stop=True)
            tasks.append(task)
        elif not tao_status and tao:
            await update_user_symbol_data(user_id, "TAOUSDT", start_stop=False)
        
        await bot.send_message(
            chat_id=user_id,
            text=result_text
        )
        await asyncio.gather(*tasks)
        return


async def generate_status_text(user_id):
    user_data = await user_start_stop.get_session_data(user_id)
    
    statuses = [
        f"Торговля для пары {format_symbol(symbol)} {'✅ торгует' if status else '⬛️ OFF'}"
        for item in user_data
        for symbol, status in item.items()
    ]
    
    if all(not any(item.values()) for item in user_data):
        return "❗️Вся торговля остановлена❗️"
    
    return "\n".join(statuses)


async def user_restart_from_admin_panel(message: Message, bot: Bot):
    user_id = message.from_user.id
    btc = await get_symbols_for_keyboard(user_id, "BTCUSDC")
    kaspa = await get_symbols_for_keyboard(user_id, "KASUSDT")
    sui = await get_symbols_for_keyboard(user_id, "SUIUSDT")
    pyth = await get_symbols_for_keyboard(user_id, "PYTHUSDT")
    dot = await get_symbols_for_keyboard(user_id, "DOTUSDT")
    tao = await get_symbols_for_keyboard(user_id, "TAOUSDT")
    
    tasks = []
    res = await get_first_message(user_id)
    if btc:
        data = await get_all_open_sell_orders_autobuy_btc(user_id, status=1)
        result = await process_order_result(data)
        task = asyncio.create_task(btc_usdc_trader(res, bot, result))
        await update_user_symbol_data(user_id, "BTCUSDC", start_stop=True)
        tasks.append(task)
    if kaspa:
        data = await get_all_open_sell_orders_autobuy(user_id, status=1)
        result = await process_order_result(data)
        task = asyncio.create_task(kaspa_trader(res, bot, result))
        await update_user_symbol_data(user_id, "KASUSDT", start_stop=True)
        tasks.append(task)
    if sui:
        data = await get_all_open_sell_orders_autobuy_from_any_table(user_id, "SUIUSDT", status=1)
        result = await process_order_result(data)
        task = asyncio.create_task(sui_trader(res, bot, result))
        await update_user_symbol_data(user_id, "SUIUSDT", start_stop=True)
        tasks.append(task)
    if pyth:
        data = await get_all_open_sell_orders_autobuy_from_any_table(user_id, "PYTHUSDT", status=1)
        result = await process_order_result(data)
        task = asyncio.create_task(pyth_trader(res, bot, result))
        await update_user_symbol_data(user_id, "PYTHUSDT", start_stop=True)
        tasks.append(task)
    if dot:
        data = await get_all_open_sell_orders_autobuy_from_any_table(user_id, "DOTUSDT", status=1)
        result = await process_order_result(data)
        task = asyncio.create_task(dot_trader(res, bot, result))
        await update_user_symbol_data(user_id, "DOTUSDT", start_stop=True)
        tasks.append(task)
    if tao:
        data = await get_all_open_sell_orders_autobuy_from_any_table(user_id, "TAOUSDT", status=1)
        result = await process_order_result(data)
        task = asyncio.create_task(dot_trader(res, bot, result))
        await update_user_symbol_data(user_id, "TAOUSDT", start_stop=True)
        tasks.append(task)
    
    await set_reset_autobuy(user_id, 0)
    await asyncio.gather(*tasks)