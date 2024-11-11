import asyncio
import logging
import traceback

from aiogram.types import Message
from aiogram import Bot
from loguru import logger
from mexc_api.common.enums import Side, OrderType

from all_mexc_methods.mexc_methods import CreateSpotConn
from all_mexc_methods.web_socket_orders import WebSocketLCientOrders
from db import update_order_by_order_id, set_order_buy_in_db, get_info_percent_profit, get_user_order_limit, \
    get_secret_key, get_access_key, get_all_open_sell_orders_autobuy, get_buy_price, update_orderafter_sale_by_order_id, \
    get_info_commission_percent
from first_reg import check_status_of_registration
from utils.additional_methods import create_time
from trading import is_working


async def handle_buy(message: Message, bot: Bot):
    user_id = message.from_user.id
    text, registration_to = await check_status_of_registration(message)
    if not registration_to:
        logger.info(
            f"Пользователь {user_id}: - просроченна дата {registration_to}")
        await message.answer(text).as_(bot)
        return
    result = await open_order_by_market(message)
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    http_mexc = CreateSpotConn(user_api_keys, user_secret_key)
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    
    if not result['autobuy']:
        web_socket_orders = WebSocketLCientOrders(api_key=user_api_keys, api_secret=user_secret_key)
        web_socket_orders.start()
        while True:
            autobuy_on = is_working.checker()
            if autobuy_on:
                return
            orders = await get_all_open_sell_orders_autobuy(user_id, 9)
            last_order_id, status, order_type = web_socket_orders.last_order()
            if orders:
                for order in orders:
                    if last_order_id == order['order_id_limit']:
                        print('dfd')
                        info = web_socket_orders.message
                        account_info = http_mexc.get_account_info_()
                        time = await create_time(info['t'])
                        qnty = info['d']['v']
                        price = info['d']['p']
                        get_money = info['d']['a']
                        total = float(get_money)
                        total_balance_usdt = http_mexc.total_after_sale
                        fee_limit = (float(price) - float(await get_buy_price(user_id, last_order_id))) * float(qnty)
                        total_open_trades = len(http_mexc.open_orders())
                        kaspa_in_orders = http_mexc.total_after_sale_Kass
                        total_free_usdt = http_mexc.total_free_usdt
                        if all([info, time, qnty, price, get_money, total, total_balance_usdt, fee_limit,
                                total_open_trades,
                                kaspa_in_orders, total_free_usdt]):
                            await update_orderafter_sale_by_order_id(user_id=user_id,
                                                                     orderId=last_order_id,
                                                                     time_sell=time,
                                                                     qty_to_sell=float(qnty),
                                                                     price_order_sell=float(price),
                                                                     total_amount_after_sale=total,
                                                                     order_id_limit=last_order_id,
                                                                     feelimit=fee_limit,
                                                                     balance_total=total_balance_usdt,
                                                                     orders_in_progress=total_open_trades,
                                                                     kaspa_in_orders=kaspa_in_orders,
                                                                     currency_for_trading=total_free_usdt,
                                                                     autobuy=2)
                            user_message = f"ПРОДАНО РЫНОК:\n" \
                                           f"{qnty} KAS по {str(price)[:8]} USDT\n" \
                                           f"<b>Получено</b> - {str(get_money)[:8]} USDT\n" \
                                           f"<b>ПРИБЫЛЬ</b> - {str(fee_limit)[:8]} USDT\n"
                            await message.answer(user_message)
                        else:
                            await message.answer("Не получилось закрыть ордер")
                        
                        break


async def open_order_by_market(message: Message):
    user_id = message.from_user.id
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    http_mexc = CreateSpotConn(user_api_keys, user_secret_key)
    order_limit_by_user = await get_user_order_limit(user_id)
    autobuy_on = is_working.checker()
    
    percent_profit = await get_info_percent_profit(user_id)
    user_commission = await get_info_commission_percent(user_id)
    
    try:
        new_order_buy = await asyncio.to_thread(http_mexc.open_new_order, side=Side.BUY,
                                                quote_order_quantity=str(order_limit_by_user))
        await asyncio.sleep(1)
        """                 Order buy details                 """
        order_buy_id = new_order_buy.get('orderId')
        order_buy_details = await asyncio.to_thread(http_mexc.order_details, order_buy_id)
        time_of_order_buy = await create_time(order_buy_details.get('updateTime'))
        avg_price = await http_mexc.get_average_price_of_order(order_buy_id)
        spend_in_usdt_for_buy = order_buy_details.get('cummulativeQuoteQty')
        """                 Create price to sell here"""
        price_to_sell = avg_price * (1 + percent_profit / 100)
        qnty_for_sell = order_buy_details.get('executedQty')
        """                 Send order into database table 'orders'     """
        while float(qnty_for_sell) <= 0:
            qnty_for_sell = order_buy_details.get('executedQty')
            price_to_sell = avg_price * (1 + percent_profit / 100)
        
        await set_order_buy_in_db(int(user_id),
                                  str(order_buy_id),
                                  time_of_order_buy,
                                  float(qnty_for_sell),
                                  float(avg_price),
                                  float(spend_in_usdt_for_buy),
                                  autobuy=9,
                                  side='BUY'
                                  )
        """                 Send sell order in database and send message to user + update order by id  """
        
        new_order_sell = await asyncio.to_thread(
            http_mexc.open_new_order, Side.SELL, OrderType.LIMIT, quantity=qnty_for_sell, price=price_to_sell
        )
        await asyncio.sleep(1)
        order_sell_id = new_order_sell.get('orderId')
        order_sell_details = http_mexc.order_details(order_sell_id)
        time_of_order_sell = await create_time(order_sell_details.get('updateTime'))
        while not all([order_sell_id, order_sell_details, time_of_order_sell]):
            order_sell_id = new_order_sell.get('orderId')
            order_sell_details = http_mexc.order_details(order_sell_id)
            time_of_order_sell = await create_time(order_sell_details.get('updateTime'))
        
        await update_order_by_order_id(int(user_id), str(order_buy_id), time_of_order_sell,
                                       float(qnty_for_sell),
                                       float(price_to_sell),
                                       None, str(order_sell_id),
                                       autobuy=9)
        
        message_order_buy = f"<b>КУПЛЕНО РЫНОК:</b>\n" \
                            f"{qnty_for_sell} KAS по {str(avg_price)[:8]} USDT\n" \
                            f"Потраченно - {str(spend_in_usdt_for_buy)[:8]} USDT\n" \
                            f"<b>ВЫСТАВЛЕННО РЫНОК:</b>\n" \
                            f"{str(qnty_for_sell)[:8]} KAS по {str(price_to_sell)[:8]} USDT\n"
        
        await asyncio.sleep(1)
        
        while not order_sell_id and avg_price:
            order_sell_id = new_order_sell.get('orderId')
            print(f'whiile not 85 orderSell - {order_sell_id}\nprice - {avg_price}')
        
        if order_sell_id and order_buy_id:
            
            await message.answer(message_order_buy)
            return {"actual_order": order_sell_id, "avg_price": avg_price, 'autobuy': autobuy_on}
        else:
            await message.answer(f'Ошибка создания ордера на продажу\n'
                                 f'buyID - {order_buy_id}\n'
                                 f'sellID - {order_sell_id}\n'
                                 f'детали  - {order_sell_details}')
    except Exception as e:
        if "Insufficient position" in str(e):
            await message.answer(
                'Недостаточно USDT для совершения покупки.\nНастраивается в /parameters.',
                parse_mode='HTML')
            return False
        else:
            print(f"Произошла другая ошибка: {e}\nbuymarket")
            logging.error(f'Произошла ошибка {e}\n Details: {15 * "-"}{traceback.print_exc()}{15 * "-"}')
            return {"actual_order": False, "avg_price": False}
