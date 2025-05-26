import datetime
import json

import httpx
import pytz
from aiogram import Bot
from loguru import logger

from services.mexc_api.all_mexc_methods.mexc_methods import CreateSpotConn
from config import PAIR_TABLE_MAP
from db_pack.db import get_all_open_sell_orders
from db_pack.db import get_all_open_sell_orders_autobuy
from db_pack.db import get_secret_key, get_access_key
from services.admins.admins_message import AdminsMessageService
from trading.session_manager import manager_kaspa, manager_btc, manager_sui, manager_pyth, manager_dot, manager_tao


async def check_user_last_autobuy_for_reset(user_id):
    all_data_from_db = await get_all_open_sell_orders_autobuy(user_id, 1)
    sorted_records = sorted(all_data_from_db, key=lambda x: x['transacttimebuy'], reverse=True)


async def sell_orders_checker(user_id: int, actual: str):
    res = await get_all_open_sell_orders(int(user_id), actual)
    for result in res:
        if result[0] == actual:
            return result[0]


async def get_user_commission(user_id):
    user_id = int(user_id)
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    
    res = CreateSpotConn(user_api_keys, user_secret_key)
    info = res.get_account_info_()
    commission = info.get('takerCommission')
    if not commission:
        commission = 0
    return commission


async def create_time(time):
    time = int(time)
    time_of_order_buy = time / 1000
    kyiv_tz = pytz.timezone('Europe/Kyiv')
    result = datetime.datetime.fromtimestamp(time_of_order_buy, tz=kyiv_tz)
    result_naive = result.replace(tzinfo=None)
    return result_naive


async def check_autobuy(user_id, selected_id):
    user_id = int(user_id)
    orders = await get_all_open_sell_orders_autobuy(user_id, 1)
    orders_9 = await get_all_open_sell_orders_autobuy(user_id, 9)
    orders.extend(orders_9)
    result = None
    if not orders:
        return False
    for row in orders:
        if row['order_id_limit'] == selected_id:
            result = row['order_id_limit']
    if result:
        return True
    return False

async def update_result_if_have_order_autobuy(user_id):
    all_data_from_db = await get_all_open_sell_orders_autobuy(user_id, 1)
    sorted_records = sorted(all_data_from_db, key=lambda x: x['transacttimebuy'], reverse=True)
    result = {'actual_order': None, 'avg_price': None}
    if len(sorted_records) > 0:
        sorted_records = sorted_records[0]
        result.update({'actual_order': sorted_records['order_id_limit'], 'avg_price': sorted_records['priceorderbuy']})
    return result


async def notify_admin(user_id, error_msg, bot: Bot, symbol: str = None):
    admin_message = AdminsMessageService()
    msg = f"❗️ У пользователя {user_id} произошла ошибка. ❗️\nОшибка: {error_msg}\nЛоги за последние два дня прикреплены."
    if symbol:
        await admin_message.send_admin_user_logger_file(user_id, symbol, bot, msg)
    else:
        await admin_message.send_admin_main_logger_file(bot, msg)


def safe_format(value: int | float = 0, precision: int = 2):
    """
    Ставит количество знаков после запятой для любого числа
    :param value : int | float - значение которое мы передаем
    :param precision : int - кол-во знаков после запятой
    """
    try:
        return f"{float(value):.{precision}f}"
    except (ValueError, TypeError):
        logger.warning(f"Ошибка при форматировании значения: {value}")
        return None
    

def user_message_returner(
                            qnty_for_sell: float,
                            price_to_sell: float,
                            total_after_sale: float,
                            fee_limit_order: float,
                            pair: str
                        ):
    if pair == "BTCUSDC":
        user_message = f"<b>ПРОДАНО:</b>\n" \
                       f"{safe_format(qnty_for_sell, 6)} {pair[:-4]} по {safe_format(price_to_sell, 2)} {pair[-4:]}\n" \
                       f"<b>Получено:</b> {safe_format(total_after_sale, 2)} {pair[-4:]}\n" \
                       f"<b>ПРИБЫЛЬ:</b> {safe_format(fee_limit_order, 4)} {pair[-4:]}\n"
    else:
        user_message = f"<b>ПРОДАНО:</b>\n" \
                       f"{safe_format(qnty_for_sell, 2)} {pair[:-4]} по {safe_format(price_to_sell, 4)} {pair[-4:]}\n" \
                       f"<b>Получено:</b> {safe_format(total_after_sale, 2)} {pair[-4:]}\n" \
                       f"<b>ПРИБЫЛЬ:</b> {safe_format(fee_limit_order, 4)} {pair[-4:]}\n"
    return user_message


def user_buy_message_returner(
        qnty_for_sell: float,
        avg_price: float,
        spend_in_usdt_for_buy: float,
        price_to_sell: str,
        pair
):
    if pair == "BTCUSDC":
        user_message = (
            f"<b>КУПЛЕНО:</b>\n"
            f"{safe_format(qnty_for_sell, 6)} {pair[:-4]} по {safe_format(avg_price, 2)} {pair[-4:]}\n"
            f"Потрачено - {safe_format(spend_in_usdt_for_buy, 2)} {pair[-4:]}\n"
            f"<b>ВЫСТАВЛЕНО:</b>\n"
            f"{safe_format(qnty_for_sell, 6)} {pair[:-4]} по {safe_format(price_to_sell, 2)} {pair[-4:]}\n"
        )
    else:
        user_message = (
            f"<b>КУПЛЕНО:</b>\n"
            f"{safe_format(qnty_for_sell, 6)} {pair[:-4]} по {safe_format(avg_price, 4)} {pair[-4:]}\n"
            f"Потрачено - {safe_format(spend_in_usdt_for_buy, 4)} {pair[-4:]}\n"
            f"<b>ВЫСТАВЛЕНО:</b>\n"
            f"{safe_format(qnty_for_sell, 6)} {pair[:-4]} по {safe_format(price_to_sell, 4)} {pair[-4:]}\n"
        )
    
    return user_message


def format_symbol(symbol: str) -> str:
    for quote in ["USDT", "USDC"]:
        if symbol.endswith(quote):
            base = symbol[:-len(quote)]
            return f"<b>{base}/{quote}</b>"
    return symbol

def format_symbol_for_keyboards(symbol: str) -> str:
    for quote in ["USDT", "USDC"]:
        if symbol.endswith(quote):
            base = symbol[:-len(quote)]
            return f"{base}/{quote}"
    return symbol


async def process_order_result(result):
    if not result:
        return None

    record = result[-1]
    
    return {
        "avg_price": record["priceorderbuy"],
        "actual_order": record["order_id_limit"]
    }

async def user_active_pair(user_id, pair):
    if pair == "KASUSDT":
        return manager_kaspa.is_active(user_id)
    elif pair == "BTCUSDC":
        return manager_btc.is_active(user_id)
    elif pair == "SUIUSDT":
        return manager_sui.is_active(user_id)
    elif pair == "PYTHUSDT":
        return manager_pyth.is_active(user_id)
    elif pair == "TAOUSDT":
        return manager_tao.is_active(user_id)
    else:
        return manager_dot.is_active(user_id)
    
    
def find_pair(symbol):
    for key in PAIR_TABLE_MAP:
        if key.startswith(symbol):
            return key
    return None

async def identify_myself() -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://ipapi.co/json/")
            location = json.loads(response.text)
            return (
                f'IP: {location["ip"]}, '
                f'Location: {location["city"]}, '
                f'{location["country_name"]}'
            )
    except:
        return "Unknown IP"