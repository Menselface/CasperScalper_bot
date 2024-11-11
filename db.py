import asyncio
import datetime
import json

from aiogram.types import Message
from asyncpg.pgproto.pgproto import timedelta
from loguru import logger

from config import db_async


"""
Тут хранятся запросы в базу данных user table
"""


async def user_exist(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        # Выполнение запроса
        result = await db_async.fetchrow('SELECT * FROM users WHERE telegram_id = $1', user_id)
        if result:
            return True
        else:
            return False
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def is_admin_checker(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        result = await db_async.fetch('SELECT telegram_id FROM users WHERE telegram_id = $1 AND is_admin = true',
                                      user_id)
        return [record['telegram_id'] for record in result]
    except Exception as e:
       logger.warning(f"Exception in db {e}")
    
    
    
async def get_all_admins():
    try:
        if db_async.pool is None:
            await db_async.connect()
        result = await db_async.fetch('SELECT telegram_id FROM users WHERE is_admin = true')
        return [record['telegram_id'] for record in result]
    except Exception as e:
       logger.warning(f"Exception in db {e}")
        
        
async def is_reset_status(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        result = await db_async.fetch('SELECT telegram_id FROM users WHERE reset_autobuy = 1 AND telegram_id = $1',
                                      user_id)
        return result
    except Exception as e:
       logger.warning(f"Exception in db {e}")
        
        

        
async def all_users_with_reset_status():
    try:
        if db_async.pool is None:
            await db_async.connect()
        result = await db_async.fetch('SELECT telegram_id FROM users WHERE reset_autobuy = 1')
        return [record['telegram_id'] for record in result]
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def add_user(user_id, first_name, last_name, username, date_time, specific_date):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.execute(
            """INSERT INTO users (telegram_id, first_name, last_name, username, registered_at, registered_to) VALUES($1, $2, $3, $4, $5, $6)""",
            user_id, first_name, last_name, username, date_time, specific_date
        )
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_timestamp_of_registration(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT registered_at FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_timestamp_end_registration(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT registered_to FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_user_stop_buy_status(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT stop_buy FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def set_access_key(user_id, access_key):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET api_key = $2 WHERE telegram_id = $1 """, user_id, access_key)
        return True
    except Exception as e:
        logger.warning(f"Exception in db {e}")
        return False
    

async def set_user_stop_autobuy(user_id : int, stop_buy: int ) -> bool:
    """Set user stop buy 1 or 0 in users table"""
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET stop_buy = $2 WHERE telegram_id = $1 """, user_id, stop_buy)
        return True
    except Exception as e:
        logger.warning(f"db error {e}")
        return False


async def get_first_message(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        res = await db_async.fetchrow("""SELECT message FROM users WHERE telegram_id = $1""", user_id)
        
        if res:
            message_data = json.loads(res['message'])
            
            # Преобразуем словарь в объект Message
            message = Message(**message_data)
            return message
        else:
            logger.info(f"No message found for user_id {user_id}")
            return None
    
    except Exception as e:
        logger.warning(f"Error retrieving message from DB: {e}")
        
        
async def set_first_message(user_id, message):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET message = $2 WHERE telegram_id = $1 """, user_id, message)
        return True
    except Exception as e:
        logger.warning(f"Exception in db {e}")
        return False

async def set_reset_autobuy(user_id, status):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET reset_autobuy = $2 WHERE telegram_id = $1 """, user_id, status)
        return True
    except Exception as e:
        logger.warning(f"Exception in db {e}")
        return False


async def set_secret_key(user_id, secret_key):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET secret_key = $2 WHERE telegram_id = $1 """, user_id, secret_key)
        return True
    except Exception as e:
        logger.warning(f"Exception in db {e}")
        return False


async def get_access_key(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT api_key FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def set_standart_user_params(user_id: int,
                                   order_limit_by: float = 30.0,
                                   percent_profit: float = 0.3,
                                   autobuy_up_sec: int = 30,
                                   auto_buy_down_perc: float = 1,
                                   taker: float = 0.02):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch(
            """UPDATE users SET order_limit_by = $2, percent_profit = $3, autobuy_up_sec = $4, auto_buy_down_perc = $5, commission_percent = $6 WHERE telegram_id = $1 """,
            user_id, order_limit_by, percent_profit, autobuy_up_sec, auto_buy_down_perc, taker)
        return True
    except Exception as e:
        logger.warning(f"Exception in db {e}")
        return False


async def get_secret_key(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT secret_key FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_await_time(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT autobuy_up_sec FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_user_order_limit(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT order_limit_by FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_info_commission_percent(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT commission_percent FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_info_percent_profit(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT percent_profit FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_info_percent_auto_buy(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT auto_buy_down_perc FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def set_user_limit_order(user_id, user_limit_order):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET order_limit_by = $2 WHERE telegram_id = $1 """, user_id,
                             user_limit_order)
        return True
    except Exception as e:
        logger.warning(f"Exception in db {e}")
        return False


async def set_percent_profiit(user_id, percent_profiit):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET percent_profit = $2 WHERE telegram_id = $1 """, user_id,
                             percent_profiit)
        return True
    except Exception as e:
        logger.warning(f"Exception in db {e}")
        return False


async def set_autobuy_up_db(user_id, autobuy_up):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET autobuy_up_sec = $2 WHERE telegram_id = $1 """, user_id, autobuy_up)
        return True
    except Exception as e:
        logger.warning(f"Exception in db {e}")
        return False


async def set_autobuy_down_db(user_id, autobuy_down):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET auto_buy_down_perc = $2 WHERE telegram_id = $1 """, user_id,
                             autobuy_down)
        return True
    except Exception as e:
        logger.warning(f"Exception in db {e}")
        return False


async def set_commission_percent(user_id, commission):
    commission = float(commission)
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch("""UPDATE users SET commission_percent = $2 WHERE telegram_id = $1 """, user_id,
                             commission)
    except Exception as e:
       logger.warning(f"Exception in db {e}")


"""
Тут хранятся запросы в базу данных orders table
"""


async def set_order_buy_in_db(user_id, orderId, time_buy, qty_to_buy, price_order_buy, total_purchace, autobuy, side):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch(
            """INSERT INTO orders (
                                telegram_id_market,
                                order_id,
                                transacttimebuy,
                                qtytobuy,
                                priceorderbuy,
                                totalamountonpurchace,
                                autobay,
                                side) VALUES($1, $2, $3, $4, $5, $6, $7, $8) """,
            user_id, orderId, time_buy, qty_to_buy, price_order_buy, total_purchace, autobuy, side)
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def update_order_by_order_id(user_id: int, orderId: str, time_sell: datetime.datetime = None,
                                   qty_to_sell: float = None,
                                   price_order_sell: float = None, total_amount_after_sale: float = None,
                                   order_id_limit: str = None, feelimit: float = None, balance_total: float = None,
                                   orders_in_progress: int = None, kaspa_in_orders: float = None,
                                   currency_for_trading: str = None,
                                   autobuy: int = None):
    user_id = int(user_id)
    orderId = str(orderId)
    time_sell = datetime.datetime.fromisoformat(time_sell) if isinstance(time_sell, str) else time_sell
    qty_to_sell = float(qty_to_sell) if qty_to_sell is not None else qty_to_sell
    price_order_sell = float(price_order_sell) if price_order_sell is not None else price_order_sell
    total_amount_after_sale = float(
        total_amount_after_sale) if total_amount_after_sale is not None else total_amount_after_sale
    order_id_limit = str(order_id_limit) if order_id_limit is not None else order_id_limit
    feelimit = float(feelimit) if feelimit is not None else feelimit
    balance_total = float(balance_total) if balance_total is not None else balance_total
    orders_in_progress = int(orders_in_progress) if orders_in_progress is not None else orders_in_progress
    kaspa_in_orders = float(kaspa_in_orders) if kaspa_in_orders is not None else kaspa_in_orders
    currency_for_trading = float(currency_for_trading) if currency_for_trading is not None else currency_for_trading
    
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        await db_async.fetch("""UPDATE orders
                                SET transacttimesell = $3,
                                    qtytosell = $4,
                                    priceordersell = $5,
                                    totalamountaftersale = $6,
                                    order_id_limit = $7,
                                    feelimitorder = $8,
                                    balance_total = $9,
                                    orders_in_progress = $10,
                                    kaspa_in_orders = $11,
                                    currency_for_trading = $12,
                                    autobay = $13
                                WHERE telegram_id_market = $1 AND order_id = $2 """,
                             user_id,
                             orderId,
                             time_sell,
                             qty_to_sell,
                             price_order_sell,
                             total_amount_after_sale,
                             order_id_limit,
                             feelimit,
                             balance_total,
                             orders_in_progress,
                             kaspa_in_orders,
                             currency_for_trading,
                             autobuy)
    except Exception as e:
       logger.warning(f"Exception in db {e}")

async def update_all_not_autobuy(user_id, status):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        await db_async.fetch("""UPDATE orders
                                SET autobay = 9
                                WHERE telegram_id_market = $1 AND autobay = $2 """,
                             user_id,
                             status)
    except Exception as e:
       logger.warning(f"Exception in db {e}")

async def update_orderafter_sale_by_order_id(user_id: int, orderId: str,
                                             time_sell: datetime.datetime = None,
                                             qty_to_sell: float = None,
                                             price_order_sell: float = None,
                                             total_amount_after_sale: float = None,
                                             order_id_limit: str = None,
                                             feelimit: float = None,
                                             balance_total: float = None,
                                             orders_in_progress: int = None,
                                             kaspa_in_orders: float = None,
                                             currency_for_trading: str = None,
                                             autobuy: int = None):
    user_id = int(user_id)
    orderId = str(orderId)
    time_sell = datetime.datetime.fromisoformat(time_sell) if isinstance(time_sell, str) else time_sell
    qty_to_sell = float(qty_to_sell) if qty_to_sell is not None else qty_to_sell
    price_order_sell = float(price_order_sell) if price_order_sell is not None else price_order_sell
    total_amount_after_sale = float(
        total_amount_after_sale) if total_amount_after_sale is not None else total_amount_after_sale
    order_id_limit = str(order_id_limit) if order_id_limit is not None else order_id_limit
    feelimit = float(feelimit) if feelimit is not None else feelimit
    balance_total = float(balance_total) if balance_total is not None else balance_total
    orders_in_progress = int(orders_in_progress) if orders_in_progress is not None else orders_in_progress
    kaspa_in_orders = float(kaspa_in_orders) if kaspa_in_orders is not None else kaspa_in_orders
    currency_for_trading = float(currency_for_trading) if currency_for_trading is not None else currency_for_trading
    autobuy = int(autobuy) if autobuy is not None else autobuy
    
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        await db_async.fetch("""UPDATE orders
                                SET transacttimesell = $3,
                                    qtytosell = $4,
                                    priceordersell = $5,
                                    totalamountaftersale = $6,
                                    order_id_limit = $7,
                                    feelimitorder = $8,
                                    balance_total = $9,
                                    orders_in_progress = $10,
                                    kaspa_in_orders = $11,
                                    currency_for_trading = $12,
                                    autobay = $13
                                WHERE telegram_id_market = $1 AND order_id_limit = $2 """,
                             user_id,
                             orderId,
                             time_sell,
                             qty_to_sell,
                             price_order_sell,
                             total_amount_after_sale,
                             order_id_limit,
                             feelimit,
                             balance_total,
                             orders_in_progress,
                             kaspa_in_orders,
                             currency_for_trading,
                             autobuy)
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_buy_price(user_id, order_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval(
            """SELECT priceorderbuy FROM orders WHERE telegram_id_market = $1 AND order_id_limit = $2  """, user_id,
            order_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def delete_order_by_user_and_order_id(user_id: int, order_id: str):
    try:
        # Проверяем, подключена ли база данных
        if db_async.pool is None:
            await db_async.connect()
        
        # Выполняем запрос на удаление записи, основываясь на идентификаторах
        result = await db_async.fetch("""DELETE FROM orders WHERE telegram_id_market = $1 AND order_id_limit = $2""",
                                      user_id, order_id)

        return True if result is None else False
    
    except Exception as e:
        # В случае ошибки выводим сообщение
        logger.warning(f"Exception in db {e}")
        return False


async def get_all_open_sell_orders(user_id, order_id):
    user_id = int(user_id)
    order_id = str(order_id)
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval(
            """SELECT order_id_limit FROM orders WHERE telegram_id_market = $1 AND order_id_limit = $2  """, user_id,
            order_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_all_open_sell_orders_autobuy(user_id, status):
    user_id = int(user_id)
    status = int(status)
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetch(
            """SELECT * FROM orders WHERE telegram_id_market = $1 AND autobay = $2  """, user_id,
            status)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")
        
async def closed_orders_for_pin_message(user_id: int, status: int, now: datetime) -> tuple:
    user_id = int(user_id)
    status = int(status)
    
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetch(
            """SELECT feelimitorder FROM orders WHERE telegram_id_market = $1 AND autobay = $2 AND  DATE(transacttimesell) = $3""", user_id,
            status, now)
        sum_of_all_deals = 0
        length = 0
        for sum_ in res:
            sum_of_all_deals += float(sum_['feelimitorder'])
            length += 1
        return sum_of_all_deals, length
    except Exception as e:
       logger.warning(f"Exception in db {e}")
        
async def get_all_id_with_registered_to_status(today: datetime) -> list:
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetch(
            """SELECT telegram_id FROM users WHERE registered_to >= $1  """, today)
        result = [i['telegram_id'] for i in res]
        return result
    except Exception as e:
        logger.info(f"Попытка достать пользователя не удалась {e}")
        
async def get_registered_to_status(user_id: int):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetch(
            """SELECT registered_to FROM users WHERE telegram_id = $1  """, user_id)
        return res[0]
    except Exception as e:
        logger.info(f"Попытка достать пользователя не удалась {e}")

async def get_registered_to(user_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval("""SELECT registered_to FROM users WHERE telegram_id = $1""", user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")
        
async def status_of_ending_of_registration(three_days_before: datetime, seven_day_after: datetime ) -> list:
    seven_day_after = seven_day_after - timedelta(seconds=5)
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetch(
            """SELECT telegram_id, registered_to FROM users WHERE registered_to <= $1 AND registered_to >= $2""", three_days_before, seven_day_after)
        return res
    except Exception as e:
        logger.info(f"Попытка достать пользователя не удалась {e}")


async def get_all_open_sell_orders_nine(user_id: int, status: int, current_price: str|float):
    try:
        user_id = int(user_id)
        status = int(status)
        current_price = float(current_price)
        
        # Рассчитываем границы диапазона (±3%)
        lower_bound = current_price * 0.97  # -3% от текущей цены
        upper_bound = current_price * 1.03  # +3% от текущей цены
        
        if db_async.pool is None:
            await db_async.connect()
        
        # Обновляем SQL-запрос для фильтрации по диапазону цены
        query = """
            SELECT * FROM orders
            WHERE telegram_id_market = $1
              AND autobay = $2
              AND priceordersell >= $3
              AND priceordersell <= $4
        """
        
        res = await db_async.fetch(query, user_id, status, lower_bound, upper_bound)
        return res
    
    except Exception as e:
        print(f"Error fetching open sell orders: {e}")
        return None


async def get_all_open_sell_orders_for_statistic(user_id):
    user_id = int(user_id)
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetch(
            """SELECT * FROM orders WHERE telegram_id_market = $1 """, user_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")


async def get_orders_from_data(user_id, oreder_id):
    user_id = int(user_id)
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchrow(
            """SELECT * FROM orders WHERE telegram_id_market = $1 AND order_id_limit = $2 """, user_id, oreder_id)
        return res
    except Exception as e:
       logger.warning(f"Exception in db {e}")
