
import datetime

from loguru import logger

from config import db_async


async def orders_update(telegram_id, **kwargs):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        if not kwargs:
            raise ValueError("No fields provided to update")
        
        set_clause = []
        values = [telegram_id]
        
        for index, (field, value) in enumerate(kwargs.items(), start=2):
            set_clause.append(f"{field} = ${index}")
            values.append(value)
        
        set_clause_str = ", ".join(set_clause)
        
        query = f"UPDATE orders_btcusdc SET {set_clause_str} WHERE telegram_id = $1"
        
        await db_async.fetch(query, *values)
        return True
    
    except Exception as e:
        logger.info(e)
        return False


async def orders_get_any(telegram_id, **kwargs):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        if not kwargs:
            raise ValueError("No fields provided to update")
        
        set_clause = []
        values = [telegram_id]  # Первый параметр — это telegram_id
        
        for index, (field, value) in enumerate(kwargs.items(), start=2):
            set_clause.append(f"{field}")
            values.append(value)
        
        set_clause_str = " AND ".join(set_clause)
        
        query = f"SELECT {set_clause_str} FROM orders_btcusdc  WHERE telegram_id = $1"
        
        res = await db_async.fetchrow(query, telegram_id)
        return res[set_clause_str]
    
    except Exception as e:
        logger.info(e)
        return False


async def update_all_not_autobuy(user_id, status):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        await db_async.fetch("""UPDATE orders_btcusdc
                                SET autobay = 9
                                WHERE telegram_id_market = $1 AND autobay = $2 """,
                             user_id,
                             status)
    except Exception as e:
        logger.warning(e)


async def update_orders_just_because(user_id, id, fee, ):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        await db_async.fetch("""UPDATE orders
                                SET feelimitorder = $3
                                WHERE telegram_id_market = $1 AND id = $2 """,
                             user_id,
                             id,
                             fee)
    except Exception as e:
        logger.warning(e)
        
        
async def set_order_buy_in_db(user_id, orderId, time_buy, qty_to_buy, price_order_buy, total_purchace, autobuy, side):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch(
            """INSERT INTO orders_btcusdc (
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
        logger.warning(e)


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
        
        await db_async.fetch("""UPDATE orders_btcusdc
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
        logger.warning(e)
    
    
async def get_buy_price(user_id, order_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval(
            """SELECT priceorderbuy FROM orders_btcusdc WHERE telegram_id_market = $1 AND order_id_limit = $2  """, user_id,
            order_id)
        return res
    except Exception as e:
        logger.warning(e)
        
async def spend_in_usdt_for_buy_order(user_id, order_id):
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchval(
            """SELECT totalamountonpurchace FROM orders_btcusdc WHERE telegram_id_market = $1 AND order_id_limit = $2  """, user_id,
            order_id)
        return res
    except Exception as e:
        logger.warning(e)


async def delete_order_by_user_and_order_id(user_id: int, order_id: str):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        result = await db_async.fetch("""DELETE FROM orders_btcusdc WHERE telegram_id_market = $1 AND order_id_limit = $2""",
                                      user_id, order_id)
        
        return True if result is None else False
    
    except Exception as e:
        logger.warning(e)
        return False


async def update_orderafter_sale_by_order_id_btc(user_id: int, orderId: str,
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
        
        await db_async.fetch("""UPDATE orders_btcusdc
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
        logger.warning(e)

async def get_orders_from_data(user_id, oreder_id):
    user_id = int(user_id)
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetchrow(
            """SELECT * FROM orders_btcusdc WHERE telegram_id_market = $1 AND order_id_limit = $2 """, user_id, oreder_id)
        return res
    except Exception as e:
        logger.warning(e)


async def get_all_open_sell_orders_nine_btc(user_id: int, status: int, current_price: str | float):
    try:
        user_id = int(user_id)
        status = int(status)
        current_price = float(current_price)
        
        lower_bound = current_price * 0.97  # -3% от текущей цены
        upper_bound = current_price * 1.03  # +3% от текущей цены
        
        if db_async.pool is None:
            await db_async.connect()
        
        query = """
            SELECT * FROM orders_btcusdc
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


async def delete_order_by_user_and_order_id_btc(user_id: int, order_id: str):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        result = await db_async.fetch("""DELETE FROM orders_btcusdc WHERE telegram_id_market = $1 AND order_id_limit = $2""",
                                      user_id, order_id)
        
        return True if result is None else False
    
    except Exception as e:
        logger.warning(e)
        return False
    

async def get_all_open_sell_orders_autobuy_btc(user_id, status):
    user_id = int(user_id)
    status = int(status)
    try:
        if db_async.pool is None:
            await db_async.connect()
        res = await db_async.fetch(
            """SELECT * FROM orders_btcusdc WHERE telegram_id_market = $1 AND autobay = $2  """, user_id,
            status)
        return res
    except Exception as e:
        logger.warning(e)