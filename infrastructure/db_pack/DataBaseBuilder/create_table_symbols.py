import asyncio

from config import db_async


create_table_query = """
    CREATE TABLE IF NOT EXISTS symbols_for_trade (
        id SERIAL PRIMARY KEY,  -- просто номер по порядку
        telegram_id BIGINT NOT NULL,  -- Идентификатор пользователя в Telegram
        symbol_name TEXT,
        order_limit_by REAL DEFAULT 5.0,  -- Сумма покупки в USDT
        percent_profit REAL DEFAULT 0.80,  -- Процент прибыли
        auto_buy_down_perc REAL DEFAULT 1.0,  -- Процент, при котором сработает АвтоБай при падении
        commission_percent REAL DEFAULT 0.10,  -- Процент комиссии биржи
        info_no_usdt INTEGER DEFAULT 0,
        reset_autobuy INTEGER DEFAULT 0, -- запасная графа
        trade_limit INTEGER DEFAULT 1000,
        start_stop BOOLEAN DEFAULT FALSE
    );
    """

drop_table_query = """
    DROP TABLE IF EXISTS symbols_for_trade;
"""

async def main():
    await db_async.connect()
    await db_async.execute(create_table_query)
    await db_async.disconnect()


asyncio.run(main())
