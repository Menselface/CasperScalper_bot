import asyncio

from loguru import logger

from config import db_async


async def user_update_symbols(telegram_id, **kwargs):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        if not kwargs:
            raise ValueError("No fields provided to update")
        
        set_clause = []
        values = [telegram_id]  # Первый параметр — это telegram_id
        
        for index, (field, value) in enumerate(kwargs.items(), start=2):
            set_clause.append(f"{field} = ${index}")
            values.append(value)
        
        set_clause_str = ", ".join(set_clause)
        
        query = f"UPDATE symbols_for_trade SET {set_clause_str} WHERE telegram_id = $1"
        
        await db_async.fetch(query, *values)
        return True
    
    except Exception as e:
        logger.info(e)
        return False


async def user_get_any_symbols(telegram_id, **kwargs):
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
        
        query = f"SELECT {set_clause_str} FROM symbols_for_trade  WHERE telegram_id = $1"
        
        res = await db_async.fetchrow(query, telegram_id)
        return res[set_clause_str]
    
    except Exception as e:
        logger.info(e)
        return False


async def user_update_by_symbol(symbol, **kwargs):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        if not kwargs:
            raise ValueError("No fields provided to update")
        
        set_clause = []
        values = [symbol]
        
        for index, (field, value) in enumerate(kwargs.items(), start=2):
            set_clause.append(f"{field} = ${index}")
            values.append(value)
        
        set_clause_str = ", ".join(set_clause)
        
        query = f"UPDATE symbols_for_trade SET {set_clause_str} WHERE symbol_name = $1"
        
        await db_async.fetch(query, *values)
        return True
    
    except Exception as e:
        logger.info(e)
        return False


async def user_get_any_by_symbol(symbol_name, **kwargs):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        if not kwargs:
            raise ValueError("No fields provided to update")
        
        set_clause = []
        values = [symbol_name]
        
        for index, (field, value) in enumerate(kwargs.items(), start=2):
            set_clause.append(f"{field}")
            values.append(value)
        
        set_clause_str = " AND ".join(set_clause)
        
        query = f"SELECT {set_clause_str} FROM symbols_for_trade  WHERE symbol_name = $1"
        
        res = await db_async.fetchrow(query, symbol_name)
        return res[set_clause_str]
    
    except Exception as e:
        logger.info(e)
        return False
    
    
async def get_all_symbols():
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        return await db_async.fetch("SELECT id, symbol_name FROM symbols_for_trade")
    
    except Exception as e:
        logger.info(e)


async def get_user_exist_with_symbol(user_id, symbol):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        result = await db_async.fetch("SELECT telegram_id, symbol_name FROM symbols_for_trade WHERE telegram_id = $1 and symbol_name = $2", user_id, symbol)
        if result:
            return result
        else:
            return False
    
    except Exception as e:
        logger.info(e)
        
        
async def add_user(user_id, symbol, start_stop=True):
    try:
        if db_async.pool is None:
            await db_async.connect()
            
        await db_async.execute(
            """INSERT INTO symbols_for_trade (telegram_id, symbol_name, start_stop) VALUES($1, $2, $3)""", user_id, symbol, start_stop)
    except Exception as e:
        logger.warning(e)


async def get_symbols_for_keyboard(user_id, symbol):
    try:
        if db_async.pool is None:
            await db_async.connect()
        
        result = await db_async.fetchrow(
            "SELECT start_stop FROM symbols_for_trade WHERE telegram_id = $1 and symbol_name = $2",
            user_id, symbol)
        if result:
            return result['start_stop']
        else:
            return None
    
    except Exception as e:
        logger.info(e)

async def get_all_user_ids_as_set():
    try:
        if db_async.pool is None:
            await db_async.connect()
        result = await db_async.fetch('SELECT telegram_id FROM symbols_for_trade')
        return {record['telegram_id'] for record in result}
    except Exception as e:
        logger.warning(e)
        return set()

async def update_start_stop(telegram_id: int, symbol_name: str, info_no_usdt: int):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.execute(
            """
            UPDATE symbols_for_trade
            SET info_no_usdt = $3
            WHERE telegram_id = $1 AND symbol_name = $2
            """,
            telegram_id,
            symbol_name,
            info_no_usdt
        )
    except Exception as e:
        logger.warning(f"Failed to update start_stop: {e}")

async def get_info_no_usdt(telegram_id: int, symbol_name: str):
    try:
        if db_async.pool is None:
            await db_async.connect()
        result = await db_async.fetchrow(
            """
            SELECT info_no_usdt
            FROM symbols_for_trade
            WHERE telegram_id = $1 AND symbol_name = $2
            """,
            telegram_id,
            symbol_name
        )
        return result["info_no_usdt"] if result else None
    except Exception as e:
        logger.warning(f"Failed to fetch info_no_usdt: {e}")
        return None


async def get_user_symbol_data(telegram_id: int, symbol_name: str, field: str):
    try:
        if db_async.pool is None:
            await db_async.connect()

        query = f"""
            SELECT {field}
            FROM symbols_for_trade
            WHERE telegram_id = $1 AND symbol_name = $2
        """

        result = await db_async.fetchrow(query, telegram_id, symbol_name)

        if not result:
            return None

        return result[field]  # Возвращаем "чистое" значение
    except Exception as e:
        logger.warning(f"Error fetching value for {field}: {e}")
        return None

async def update_user_symbol_data(telegram_id: int, symbol_name: str, **kwargs):
    try:
        if db_async.pool is None:
            await db_async.connect()

        if not kwargs:
            raise ValueError("No fields provided to update")

        set_clause = []
        values = [telegram_id, symbol_name]  # Первые два параметра — telegram_id и symbol_name

        for index, (field, value) in enumerate(kwargs.items(), start=3):
            set_clause.append(f"{field} = ${index}")
            values.append(value)

        set_clause_str = ", ".join(set_clause)

        query = f"""
            UPDATE symbols_for_trade
            SET {set_clause_str}
            WHERE telegram_id = $1 AND symbol_name = $2
        """

        await db_async.execute(query, *values)
        return True

    except Exception as e:
        logger.warning(f"Error updating data: {e}")
        return False

async def set_standart_user_params(
                                    telegram_id: int,
                                    symbol_name: int,
                                    order_limit_by: float = 5.0,
                                    percent_profit: float = 0.8,
                                    auto_buy_down_perc: float = 1,
                                    trade_limit: int = 1000000,
                                    taker: float = 0.1
                                    ):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch(
            """UPDATE symbols_for_trade SET order_limit_by = $3, percent_profit = $4, auto_buy_down_perc = $5, trade_limit = $6, commission_percent = $7 WHERE symbol_name = $2 AND telegram_id = $1 """,
            telegram_id, symbol_name, order_limit_by, percent_profit, auto_buy_down_perc, trade_limit, taker)
        return True
    except Exception as e:
        logger.warning(e)
        return False
    
async def set_standart_user_params_for_all(user_id: int,
                                   order_limit_by: float = 5.0,
                                   percent_profit: float = 0.8,
                                   auto_buy_down_perc: float = 1,
                                    trade_limit: int = 1000000,
                                   taker: float = 0.1):
    try:
        if db_async.pool is None:
            await db_async.connect()
        await db_async.fetch(
            """UPDATE symbols_for_trade SET order_limit_by = $2, percent_profit = $3, auto_buy_down_perc = $4, trade_limit = $5, commission_percent = $6 WHERE telegram_id = $1 """,
            user_id, order_limit_by, percent_profit, auto_buy_down_perc, trade_limit, taker)
        return True
    except Exception as e:
        logger.warning(e)
        return False