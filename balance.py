import requests
from aiogram import Bot
from aiogram.types import Message

import datetime
from loguru import logger

from all_mexc_methods.AccountMexc import AccountMexcMethods
from db import get_all_open_sell_orders_autobuy, get_secret_key, get_access_key, get_info_commission_percent
from first_reg import check_status_of_registration


async def handle_balance(message: Message, bot: Bot):
    user_id = message.from_user.id
    text, registration_to = await check_status_of_registration(message)
    kaspa_url = 'https://api.mexc.com/api/v3/ticker/price?symbol=KASUSDT'
    kaspa_response = requests.get(kaspa_url)
    kaspa_price_data = kaspa_response.json()
    kaspa_price = f"{float(kaspa_price_data['price']):.6f}"
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    current_date = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    all_data_from_db = await get_all_open_sell_orders_autobuy(user_id, 1)
    all_data_from_db.extend(await get_all_open_sell_orders_autobuy(user_id, 9))
    commission = await get_info_commission_percent(user_id)
    total_orders = len(all_data_from_db)
    acc_info = AccountMexcMethods(user_api_keys, user_secret_key)
    await acc_info.get_account_info_()
    total_usdt = acc_info.total_free_usdt
    total_locked_in_kasp = acc_info.locked
    total_locked_in_usdt = acc_info.usdt_locked
    total_free_kaspa = acc_info.total_after_sale_Kass
    print(type(total_free_kaspa))
    total_result_usdt = total_usdt + total_locked_in_usdt + (float(total_free_kaspa) * float(kaspa_price))
    dfdf = 0
    for order in all_data_from_db:
        try:
            total_result_usdt += order['qtytosell'] * order['priceordersell'] - commission
            dfdf += order['qtytosell']
        except Exception as e:
            total_orders -= 1
            logger.warning(f"User {user_id} ошибка у ордера {order['order_id']} {e}")
            continue
    
    
    text = (f"<b>БАЛАНС</b> {current_date}\n"
            f"Курс Каспа: {kaspa_price}\n"
            f"Количество ордеров: {total_orders}\n\n"
            f"<b>USDT</b>\n"
            f"Доступно: {total_usdt:.2f}\n"
            f"В ордерах: {total_locked_in_usdt:.2f}\n\n"
            f"<b>KASPA</b>\n"
            f"Доступно: {total_free_kaspa:.2f}\n"
            f"В ордерах: {dfdf:.2f}\n\n"
            f"Итого: {total_result_usdt:.2f}")
    await bot.send_message(user_id, text)
    