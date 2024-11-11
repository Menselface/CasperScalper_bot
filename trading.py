import asyncio
import os
import shutil
import time
import datetime
from pprint import pprint

import requests
from asyncpg.pgproto.pgproto import timedelta
from loguru import logger

from aiogram import Bot
from aiogram.types import Message, FSInputFile
from aiogram import Bot
import logging
import asyncio

from mexc_api.common.enums import Side
from mexc_api.common.exceptions import MexcAPIError
from websocket import WebSocketConnectionClosedException

from all_mexc_methods.mexc_methods import *

from all_mexc_methods.web_socket_orders import WebSocketLCientOrders
from all_mexc_methods.web_socket_price import WebSocketPrice
from first_reg import check_status_of_registration
from db import get_access_key, get_secret_key, get_info_percent_profit, set_order_buy_in_db, update_order_by_order_id, \
    get_info_percent_auto_buy, get_await_time, get_all_open_sell_orders, update_orderafter_sale_by_order_id, \
    get_buy_price, get_user_order_limit, get_all_open_sell_orders_autobuy, get_info_commission_percent, is_reset_status, \
    set_reset_autobuy, update_all_not_autobuy, get_orders_from_data, get_all_open_sell_orders_nine, \
    get_user_stop_buy_status, set_user_stop_autobuy, delete_order_by_user_and_order_id, \
    get_all_id_with_registered_to_status, get_registered_to_status, get_all_admins
from keyboards import user_commission_choices
from utils.additional_methods import sell_orders_checker, get_user_commission, create_time, AutoBuy, check_autobuy, \
    check_user_last_autobuy_for_reset, update_result_if_have_order_autobuy, remove_user_from_is_working_status
from all_mexc_methods.AccountMexc import AccountMexcMethods, CreateSpotConn_

websocket_logger = logging.getLogger('pymexc.base_websocket')
websocket_logger.setLevel(logging.WARNING)

is_working = AutoBuy()

LOGS_DIR = "logs"

# Создание директории для логов, если она не существует
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

async def start_orders_check(message, bot):
    asyncio.create_task(orders_checker_onlly_nine(message, bot))

user_log_file = f"{LOGS_DIR}/logers.log"
if not os.path.exists(user_log_file):
    logger.add(user_log_file, rotation="10 MB", retention="5 days", compression="gz", level="INFO")


async def notify_admin(user_id, error_msg, bot: Bot):
    log_file = f'logs/logers.log'
    temp_log_file = f'logs/logers_сopy.log'
    shutil.copy(log_file, temp_log_file)
    user_agreements = FSInputFile('logs/logers_сopy.log', filename='logers_сopy.log')
    all_admins = await get_all_admins()
    for admin_id in all_admins:
        try:
            await bot.send_document(
                chat_id=admin_id,
                document=user_agreements,
                caption=f"❗️ У пользователя {user_id} произошла ошибка. ❗️\nОшибка: {error_msg}\nЛоги прикреплены.")
            
        except Exception as e:
            logger.critical(f"Не могу скинуть файл {e} ")
    os.remove(temp_log_file)

@logger.catch()
async def handle_autobuy(message: Message, bot: Bot):
    global is_working
    user_id = message.from_user.id
    stop_stats = await get_user_stop_buy_status(user_id)
    if stop_stats == 1:
        await set_user_stop_autobuy(user_id=user_id, stop_buy=0)
        logger.info(
            f'Пользователь {user_id} -\n Resset status stop buy nto 0 ')
    no_repeat = True
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    text, registration_to = await check_status_of_registration(message)
    account_spot_conn = CreateSpotConn_(user_api_keys, user_secret_key)
    s = account_spot_conn.get_account_info_()
    if 'Api key info invalid' in s:
        await bot.send_message(user_id, f'Ошибка в апи ключах, сообщите в поддержку @AlisaStrange.')
        logger.warning(f"{user_id} Ошибка в апи ключах - {user_api_keys}, {user_secret_key}")
        await notify_admin(user_id, str(s), bot)
        is_working.remove_user(user_id)
        is_working.is_working = False
        return
        
    if user_id in is_working.user_autobuy_status:
        logger.info(f"User {user_id} is already running a session. Stopping previous session.")
        is_working.double_user.update({'id': user_id, 'status': True})

        logger.info(f"User : {user_id} is push 'go_work' so now we ending previous session")
        await asyncio.sleep(2)
    else:
        if not registration_to:
            logger.info(
                f"Пользователь {user_id}: - просроченна дата {registration_to}")
            await message.answer(text).as_(bot)
            return
        await start_orders_check(message, bot)

    while True:
        
        result = {'actual_order': None, 'avg_price': None}
        if await is_reset_status(user_id):
            result = await get_very_last_autobuy(message, bot, user_id)
            logger.info(
                f"Пользователь {user_id}: перезапуск через колбасу {result}")
            await set_reset_autobuy(user_id, 0)
        if not result['actual_order'] and not result['avg_price']:
            logger.info(
                f"Пользователь {user_id}: нет текущего автобай, идем открывать новый")
            result = await open_order(message, bot)
            logger.info(
                f"Пользователь {user_id}: Новый ордер открыт")
            if result['not_money']:
                no_repeat = False
                result = await get_very_last_autobuy(message, bot, user_id)
                logger.info(
                    f"Пользователь {user_id}: Открытие ордера вернуло недостаток средств, ставим флаг \nno_repeat = {no_repeat}")
        
        avg_price = result.get('avg_price')
        actual_order_id = result.get('actual_order')
        logger.info(
        f"Пользователь {user_id}: avg_price: {avg_price} actual_order_id: {actual_order_id}")
        
        """    Connect to websockets price and orders status      """
        real_time_price = WebSocketPrice(api_key=user_api_keys, api_secret=user_secret_key)
        
        await asyncio.gather(
            asyncio.to_thread(real_time_price.start),
        )
        while True:
            
            """    Connect to websockets price and orders status      """
            text, registration_to = await check_status_of_registration(message)
            if not registration_to:
                logger.info(
                    f"Пользователь {user_id}: - просроченна дата {registration_to}")
                await message.answer(text).as_(bot)
                is_working.is_working = False
                is_working.remove_user(user_id)
                return
            
            await asyncio.sleep(1)
            stop_stats = await get_user_stop_buy_status(user_id)
            is_working.is_working = True
            is_working.add_user_session(user_id)
            percent_auto_buy = await get_info_percent_auto_buy(user_id)
            logger.info(
            f"Пользователь {user_id}: получил процент прибыли - {percent_auto_buy}")
            if avg_price and percent_auto_buy:
                threshold_price = avg_price * (1 - percent_auto_buy / 100)
                logger.info(
                    f"Пользователь {user_id}: получил цену падения - {threshold_price}")
            else:
                logging.error(f" - 69")
                logger.warning(
                    f"Пользователь {user_id}: не получил цену падения - avg_price: {avg_price}\n actual_order_id:{actual_order_id}")
                await asyncio.sleep(2)
                no_repeat = False
                threshold_price = 1000000000
                
            try:
                current_price = await real_time_price.get_price()
                logger.info(
                    f"Пользователь {user_id}: текущая цена - {current_price}")
                
                if not current_price:
                    while not current_price:
                        await asyncio.sleep(1)
                        current_price = real_time_price.get_price()
                
                """Проверка на цену"""
                if float(current_price) <= float(threshold_price) and no_repeat:
                    await message.answer(
                        f'🔽 УВЕДОМЛЕНИЕ 🔽\n️KAS упала до цены {round(threshold_price, 6)} (на {round(percent_auto_buy, 2)} % от {round(avg_price, 6)})').as_(
                        bot)
                    logger.info(
                        f"Пользователь {user_id}: цена KAS упала до {current_price}, ниже порога {threshold_price}.")
                    treshold_result = await open_order(message, bot)
                    await asyncio.sleep(1)
                    if treshold_result['avg_price'] and treshold_result['actual_order']:
                        avg_price = treshold_result.get('avg_price')
                        actual_order_id = treshold_result.get('actual_order')
                        logger.info(
                            f"Пользователь {user_id}: новый ордер {actual_order_id}, новая цена {avg_price}.")
                        continue
                    elif treshold_result['not_money']:
                        no_repeat = False
                        logger.info(
                            f"Пользователь {user_id}: нехватка денег, флаг no_repeat = {no_repeat}")
                        continue
                    
                    else:
                        await message.answer(
                            f'Произошла ошибка при  попытке купить при падении {treshold_result.get("e")}').as_(bot)
                        logger.critical(
                            f"Пользователь {user_id}: Произошла ошибка при  попытке купить при падении")
                        logger.critical(f"Ошибка у пользователя {user_id}: {str(e)}")
                        await notify_admin(user_id, str(e), bot)
                        is_working.is_working = False
                        is_working.remove_user(user_id)
                        return
                if is_working.double_user.get('id') == user_id:
                    logger.warning(f"User: {user_id} is reset autobuy and return")
                    is_working.double_user.pop('id', None)  # Удаляем ключ 'id' из словаря
                    is_working.double_user.pop('status', None)  # Удаляем ключ 'status' из словаря
                    return
                if stop_stats == 1:
                    is_working.remove_user(user_id)
                    is_working.is_working = False
                    logger.info(f'Пользователь {user_id} - @{message.from_user.username if message.from_user.username else "None"}:\n Остановил покупки ')
                    return
                    
                is_autobuy_was_closed = await orders_checker(message, bot, current_order_id=actual_order_id)
                await asyncio.sleep(3)
                if is_autobuy_was_closed.get('autobuy_is_closed'):
                    logger.info(f"Пользователь {user_id}: автобай был закрыт, номер - {actual_order_id}")
                    delay_time = await get_await_time(user_id)
                    await asyncio.sleep(delay_time)
                    break
                elif is_autobuy_was_closed.get('autobuy_was_cancelled'):
                    await bot.send_message(user_id, "Торги остановлены. GENERAL ордер на бирже отсутствует. Чтобы продолжить торги Нажми в меню /start_trade.  Если Вы не отменяли в ручную ордер на бирже - сообщите об ошибке в поддержку @RomaKnyazeff")
                    is_working.remove_user(user_id)
                    is_working.is_working = False
                    return
                else:
                    logger.info(f"Пользователь {user_id}: автобай не закрыт, начинаем цикл заново")
                    continue
            
            except Exception as e:
                if "ping/pong timed out" in str(e):
                    logger.warning(f"Пользователь {user_id}: вебсокет не дает ответ - {e}, пробуем переподключиться")
                    real_time_price = WebSocketPrice(api_key=user_api_keys, api_secret=user_secret_key)
                    
                    await asyncio.gather(
                        asyncio.to_thread(real_time_price.start),
                    )
                    continue
                elif "Insufficient position" in str(e):
                    logger.info(f'{user_id}' )
                    no_repeat = False
                    await message.answer(
                        'Недостаточно USDT для совершения покупки.\nНастраивается в /parameters.').as_(
                        bot)
                    logger.info(f"Пользователь {user_id}: недостаточно денег на счету - {e}")
                    continue
                elif "argument of type 'MexcAPIError' is not iterable" in e:
                    logger.warning(f"Пользователь {user_id}: непонятная ошибка, начнем заново - {e}")
                    continue
                elif "Api key info invalid" in str(e):
                    await bot.send_message(user_id, 'Ошибка в апи ключах, сообщите в поддержку @romaknyazeff.')
                    logger.warning(f"{user_id} Ошибка в апи ключах")
                    await notify_admin(user_id, str(e), bot)
                    is_working.remove_user(user_id)
                    is_working.is_working = False
                else:
                    logger.critical(f"Ошибка у пользователя {user_id}: {str(e)}")
                    await notify_admin(user_id, str(e), bot)
                    is_working.remove_user(user_id)
                    is_working.is_working = False
                    return


async def open_order(message: Message, bot):
    user_id = message.from_user.id
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    http_mexc = CreateSpotConn(user_api_keys, user_secret_key)
    order_limit_by_user = await get_user_order_limit(user_id)
    await orders_checker(message, bot, user_id)
    
    percent_profit = await get_info_percent_profit(user_id)
    user_commission = await get_info_commission_percent(user_id)
    
    try:
        await update_all_not_autobuy(user_id, 1)
        new_order_buy = await asyncio.to_thread(http_mexc.open_new_order, side=Side.BUY,
                                                quote_order_quantity=str(order_limit_by_user))
        await asyncio.sleep(1)
        """                 Order buy details                 """
        order_buy_id = new_order_buy.get('orderId')
        logger.info(f"Пользователь {user_id}: Открытие нового ордера {order_buy_id}")
        order_buy_details = await asyncio.to_thread(http_mexc.order_details, order_buy_id)
        time_of_order_buy = await create_time(order_buy_details.get('updateTime'))
        avg_price = await http_mexc.get_average_price_of_order(order_buy_id)
        spend_in_usdt_for_buy = order_buy_details.get('cummulativeQuoteQty')
        """                 Create price to sell here"""
        price_to_sell = avg_price * (1 + percent_profit / 100)
        qnty_for_sell = order_buy_details.get('executedQty')
        """                 Send order into database table 'orders'     """
        if float(qnty_for_sell) <= 0:
            while float(qnty_for_sell) <= 0:
                qnty_for_sell = order_buy_details.get('executedQty')
                price_to_sell = avg_price * (1 + (percent_profit + user_commission) / 100)
        await set_order_buy_in_db(int(user_id),
                                  str(order_buy_id),
                                  time_of_order_buy,
                                  float(qnty_for_sell),
                                  float(avg_price),
                                  float(spend_in_usdt_for_buy),
                                  autobuy=1,
                                  side='BUY'
                                  )
        """                 Send sell order in database and send message to user + update order by id  """
        
        new_order_sell = await asyncio.to_thread(
            http_mexc.open_new_order, Side.SELL, OrderType.LIMIT, quantity=qnty_for_sell, price=price_to_sell
        )
        
        await asyncio.sleep(1)
        order_sell_id = new_order_sell.get('orderId')
        logger.info(f"Пользователь {user_id}: Открытие нового ордера продажа {order_sell_id}")
        order_sell_details = http_mexc.order_details(order_sell_id)
        time_of_order_sell = await create_time(order_sell_details.get('updateTime'))
        while not all([order_sell_id, order_sell_details, time_of_order_sell]):
            logger.info(f"Пользователь {user_id}: ждет ответа от биржи")
            order_sell_id = new_order_sell.get('orderId')
            order_sell_details = http_mexc.order_details(order_sell_id)
            time_of_order_sell = await create_time(order_sell_details.get('updateTime'))
        
        await update_order_by_order_id(int(user_id), str(order_buy_id), time_of_order_sell,
                                       float(qnty_for_sell),
                                       float(price_to_sell),
                                       None, str(order_sell_id), autobuy=1)
        
        message_order_buy = f"<b>КУПЛЕНО:</b>\n" \
                            f"{order_buy_id}\n" \
                            f"{qnty_for_sell} KAS по {round(float(avg_price), 6)} USDT\n" \
                            f"Потраченно - {round(float(spend_in_usdt_for_buy), 6)} USDT\n" \
                            f"<b>ВЫСТАВЛЕННО:</b>\n" \
                            f"{round(float(qnty_for_sell), 6)} KAS по {round(float(price_to_sell), 6)} USDT\n"
        
        await asyncio.sleep(1)
        
        while not order_sell_id and avg_price:
            order_sell_id = new_order_sell.get('orderId')
        
        if order_sell_id and order_buy_id:
            
            await message.answer(message_order_buy).as_(bot)
            logger.info(f"Пользователь {user_id}: получил сообщение о покупке Функция вернула коретные данные  Продажа - {order_sell_id}, Покупка - {order_buy_id}, цена - {avg_price}")
            return {"actual_order": order_sell_id, "avg_price": avg_price, 'not_money': False}
        else:
            warning = (f'Ошибка создания ордера на продажу\n'
                                 f'buyID - {order_buy_id}\n'
                                 f'sellID - {order_sell_id}\n'
                                 f'детали  - {order_sell_details}')
            
            logger.critical(f"Ошибка у пользователя:\n {user_id}: {warning}")
            await notify_admin(user_id, warning, bot)
    except Exception as e:
        if "Insufficient position" in str(e):
            await message.answer(
                'Недостаточно USDT для совершения покупки.\nНастраивается в /parameters.',
                parse_mode='HTML').as_(bot)
            logger.info(
                f"Пользователь {user_id}:Недостаточно USDT для совершения покупки actual_order: False, avg_price: False, not_money: True")
            return {"actual_order": False, "avg_price": False, 'not_money': True}
        else:
            logger.critical(f"Ошибка у пользователя {user_id}: {str(e)}")
            await notify_admin(user_id, str(e), bot)
            is_working.remove_user(user_id)
            is_working.is_working = False


async def orders_checker(message: Message, bot, user_id: int = None, current_order_id: str = None):
    if not user_id:
        user_id = message.from_user.id
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    http_mexc = AccountMexcMethods(user_api_keys, user_secret_key)
    not_founds = []
    result = {
        'autobuy_is_closed': False,
        'autobuy_was_cancelled': False,
        '400': not_founds
    }
    
    user_orders_from_table = await get_all_open_sell_orders_autobuy(user_id, 1)
    closed_orders = set()
    logger.info(
        f"Пользователь {user_id}: Проверка закрытых ордеров, текуший автобай = {current_order_id}")
    for record in user_orders_from_table:
        try:
            order = await http_mexc.get_order_status(record['order_id_limit'])
            status = order.get('status')
            logger.info(status)
            if status == 'FILLED':
                logger.critical(f"Данные о закрытом ордере {order}")
    
                
                totalamountonpurchace = record['totalamountonpurchace']
                order_buy_id = order.get('orderId')
                logger.info(
                    f"Пользователь {user_id}: закрыт ордер {order_buy_id}")
                if current_order_id == order_buy_id:
                    result.update({'autobuy_is_closed': True})
                    logger.info(
                        f"Пользователь {user_id}: закрыт ордер autobuy")
                    
                time_of_order_sell = await create_time(order.get('updateTime'))
                qnty_for_sell = order.get('executedQty')
                price_to_sell = order.get('price')
                total_after_sale = order.get('origQuoteOrderQty')
                account_info = await http_mexc.get_account_info_()
                fee_limit_order = float(total_after_sale) - float(totalamountonpurchace)
                total_balance_usdt = http_mexc.total_after_sale or 0
                total_open_trades = len(await http_mexc.get_open_orders()) or 0
                kaspa_in_orders = http_mexc.total_after_sale_Kass or 0
                total_free_usdt = http_mexc.total_free_usdt or 0
                
                await update_orderafter_sale_by_order_id(int(user_id), str(order_buy_id),
                                                         time_of_order_sell,
                                                         float(qnty_for_sell),
                                                         float(price_to_sell),
                                                         order_id_limit=record['order_id_limit'],
                                                         autobuy=2,
                                                         total_amount_after_sale=total_after_sale,
                                                         feelimit=fee_limit_order,
                                                         balance_total=total_balance_usdt,
                                                         orders_in_progress=total_open_trades,
                                                         kaspa_in_orders=kaspa_in_orders,
                                                         currency_for_trading=total_free_usdt
                                                         )
                closed_orders.add(order_buy_id)
            if status == 'CANCELED':
                await delete_order_by_user_and_order_id(user_id, current_order_id)
                logger.info(f"User {user_id} canceled order with status 1 {order}")
                result.update({'autobuy_was_cancelled': True})
        
        except Exception as e:
            logger.info(f"Ордер попал в исключение - {e}")
            continue
        else:
            pass
    await send_messages_to_user(message, closed_orders, bot)
    logger.info(f"Пользователю: {user_id} возвращаем {result}")
    return result


async def send_messages_to_user(message: Message, orders, bot):
    user_id = message.from_user.id
    for i in orders:
        try:
            res = await get_orders_from_data(user_id, i)
            order_buy_id = res['order_id']
            qnty_for_sell = res['qtytosell']
            price_to_sell = res['priceordersell']
            total_after_sale = res['totalamountaftersale']
            fee_limit_order = res['feelimitorder']
            user_message = f"ПРОДАНО:\n" \
                           f"{order_buy_id}\n" \
                           f"{round(qnty_for_sell)} KAS по {round(float(price_to_sell), 6)} USDT\n" \
                           f"<b>Получено</b> - {round(float(total_after_sale), 6)} USDT\n" \
                           f"<b>ПРИБЫЛЬ</b> - {round(fee_limit_order, 6)} USDT\n"
            await message.answer(user_message, parse_mode="HTML").as_(bot)
            logger.info(f"Отправили сообщение {order_buy_id}")
        except Exception as e:
            logger.info(f"Ошибка при отправке сообшения {e}")
        


async def get_very_last_autobuy(message, bot, user_id):
    result = {'actual_order': None, 'avg_price': None}
    all_data_from_db = await get_all_open_sell_orders_autobuy(user_id, 1)
    sorted_records = sorted(all_data_from_db, key=lambda x: x['transacttimebuy'], reverse=True)
    logger.info(f"Получаем последний ордер, сортируем {sorted_records}")
    if len(sorted_records) > 0:
        sorted_records = sorted_records[0]
        order_exist = await orders_checker(message, bot, current_order_id=sorted_records['order_id_limit'])
        if sorted_records not in order_exist['400']:
            result.update({'actual_order': sorted_records['order_id_limit'],
                           'avg_price': sorted_records['priceorderbuy']})
            logger.info(f"Получаем последний ордер, возвращаем {result}")
            return result
    logger.info(f"Получаем последний ордер, возвращаем {result}")
    return result


async def orders_checker_onlly_nine(message: Message, bot, user_id: int = None):
    if not user_id:
        user_id = message.from_user.id
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    http_mexc = AccountMexcMethods(user_api_keys, user_secret_key)
    user_commission = await get_user_commission(user_id)
    kaspa_url = 'https://api.mexc.com/api/v3/ticker/price?symbol=KASUSDT'
    while True:
        user_alive_status = await get_registered_to_status(user_id)
        today = datetime.datetime.now()
        max_alive_user = user_alive_status['registered_to'] + timedelta(days=7)
        if today.strftime('%Y-%m-%d %H:%M') == max_alive_user.strftime('%Y-%m-%d %H:%M'):
            logger.info(f"Коннечная остановка у пользователя {user_id}")
            return
        kaspa_response = requests.get(kaspa_url)
        kaspa_price_data = kaspa_response.json()
        current_price = float(kaspa_price_data['price'])
        logger.info(f"Текущая цена каспы - {current_price} {type(current_price)}")
        
        user_orders_from_table_nine = await get_all_open_sell_orders_nine(user_id, 9, current_price)
        closed_orders = set()
        logger.info(
            f"Пользователь {user_id}: Проверка закрытых ордеров статуса 9")
        for record in user_orders_from_table_nine:
            try:
                order = await http_mexc.get_order_status(record['order_id_limit'])
                status = order.get('status')
                if status == 'FILLED':
    
                    totalamountonpurchace = record['totalamountonpurchace']
                    order_buy_id = order.get('orderId')
                    logger.info(
                        f"Пользователь {user_id}: закрыт ордер {order_buy_id}")
    
                    time_of_order_sell = await create_time(order.get('updateTime'))
                    qnty_for_sell = order.get('executedQty')
                    price_to_sell = order.get('price')
                    total_after_sale = order.get('origQuoteOrderQty')
                    account_info = await http_mexc.get_account_info_()
                    fee_limit_order = float(total_after_sale) - float(totalamountonpurchace) - float(user_commission)
                    total_balance_usdt = http_mexc.total_after_sale or 0
                    total_open_trades = len(await http_mexc.get_open_orders()) or 0
                    kaspa_in_orders = http_mexc.total_after_sale_Kass or 0
                    total_free_usdt = http_mexc.total_free_usdt or 0
    
                    await update_orderafter_sale_by_order_id(int(user_id), str(order_buy_id),
                                                             time_of_order_sell,
                                                             float(qnty_for_sell),
                                                             float(price_to_sell),
                                                             order_id_limit=record['order_id_limit'],
                                                             autobuy=2,
                                                             total_amount_after_sale=total_after_sale,
                                                             feelimit=fee_limit_order,
                                                             balance_total=total_balance_usdt,
                                                             orders_in_progress=total_open_trades,
                                                             kaspa_in_orders=kaspa_in_orders,
                                                             currency_for_trading=total_free_usdt
                                                             )
                    closed_orders.add(order_buy_id)
                if status == 'CANCELED':
                    await delete_order_by_user_and_order_id(user_id, record['order_id_limit'])
                    logger.info(f"User {user_id} canceled order with status 9 {order}")
                
                
            except Exception as e:
                logger.info(f"Ордер попал в исключение - {e}")
                continue
            else:
                pass
        await send_messages_to_user(message, closed_orders, bot)
        logger.info(f"Пользователь: {user_id} проверил ордера статус 9")
        await asyncio.sleep(20)