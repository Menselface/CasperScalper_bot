from datetime import datetime

from loguru import logger

from config import db_async, PAIR_TABLE_MAP


async def update_all_not_autobuy_any_table(user_id: int, status:int, symbol: str):
    table_name = PAIR_TABLE_MAP.get(symbol)
    
    if not table_name:
        raise ValueError(f"Unsupported pair: {table_name}")
    
    try:
        if db_async.pool is None:
            await db_async.connect()
        query = f"""UPDATE {table_name}
                                SET autobay = 9
                                WHERE telegram_id_market = $1 AND autobay = $2"""
        
        await db_async.fetch(query,
                             user_id,
                             status)
    except Exception as e:
        logger.warning(e)
        
async def set_order_buy_any_table(symbol, telegram_id_market, order_id, transacttimebuy, qtytobuy, priceorderbuy, totalamountonpurchace, autobay, side):
    table_name = PAIR_TABLE_MAP.get(symbol)
    
    if not table_name:
        raise ValueError(f"Unsupported pair: {symbol}")
    
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        query = f"""
                    INSERT INTO {table_name}(
                        telegram_id_market,
                        order_id,
                        transacttimebuy,
                        qtytobuy,
                        priceorderbuy,
                        totalamountonpurchace,
                        autobay,
                        side
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
        
        await db_async.execute(
            query,
            telegram_id_market,
            order_id,
            transacttimebuy,
            qtytobuy,
            priceorderbuy,
            totalamountonpurchace,
            autobay,
            side,
        )
    except Exception as e:
        logger.warning(e)


async def update_order_by_order_id_any_table(symbol: str, user_id: int, orderId: str, time_sell: datetime = None,
                                   qty_to_sell: float = None,
                                   price_order_sell: float = None, total_amount_after_sale: float = None,
                                   order_id_limit: str = None, feelimit: float = None, balance_total: float = None,
                                   orders_in_progress: int = None, kaspa_in_orders: float = None,
                                   currency_for_trading: str = None,
                                   autobuy: int = None):
    user_id = int(user_id)
    orderId = str(orderId)
    time_sell = datetime.fromisoformat(time_sell) if isinstance(time_sell, str) else time_sell
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
        
        table_name = PAIR_TABLE_MAP.get(symbol)
        
        if not table_name:
            raise ValueError(f"Unsupported pair: {symbol}")
            
        query = f"""UPDATE {table_name}
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
                                WHERE telegram_id_market = $1 AND order_id = $2 """
        
        await db_async.fetch(query,
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
        
async def get_buy_price_any_table(symbol, user_id, order_id):
    table_name = PAIR_TABLE_MAP.get(symbol)
    
    if not table_name:
        raise ValueError(f"Unsupported pair: {symbol}")
    
    try:
        if db_async.pool is None:
            await db_async.connect()
            
        query = f"""SELECT priceorderbuy FROM {table_name} WHERE telegram_id_market = $1 AND order_id_limit = $2"""
        res = await db_async.fetchval(query, user_id, order_id)
        return res
    except Exception as e:
        logger.warning(e)
        
        
async def spend_in_usdt_for_buy_order_any_table(symbol, user_id, order_id):
    table_name = PAIR_TABLE_MAP.get(symbol)
    
    if not table_name:
        raise ValueError(f"Unsupported pair: {symbol}")
    
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        query = f"""SELECT totalamountonpurchace FROM {table_name} WHERE telegram_id_market = $1 AND order_id_limit = $2"""
        res = await db_async.fetchval(query, user_id, order_id)
        
        return res
    except Exception as e:
        logger.warning(e)


async def delete_order_by_user_and_order_id_from_any_table_by_symbol(symbol, user_id: int, order_id_limit: str):
    table_name = PAIR_TABLE_MAP.get(symbol)
    
    if not table_name:
        raise ValueError(f"Unsupported pair: {symbol}")
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        
        query = f"""DELETE FROM {table_name} WHERE telegram_id_market = $1 AND order_id_limit = $2"""
        
        result = await db_async.fetch(query, user_id, order_id_limit)
        return True
    
    
    except Exception as e:
        logger.warning(e)
        return False