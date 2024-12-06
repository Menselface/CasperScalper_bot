import asyncio

from config import db_async


create_table_query = """
    CREATE TABLE IF NOT EXISTS orders_btcusdc (
        id SERIAL PRIMARY KEY,  -- просто номер по порядку
        telegram_id_Market BIGINT NOT NULL,  -- Идентификатор пользователя в Telegram
        order_id TEXT,
        side TEXT,
        transactTimeBUY TIMESTAMP,
        QtyToBuy REAL,
        PriceOrderBUY REAL,
        TotalAmountOnPurchace REAL,
        AUTOBAY INT,
        order_id_Limit TEXT,
        transactTimeSell TIMESTAMP,
        QtyToSell REAL,
        PriceOrderSell REAL,
        TotalAmountAfterSale REAL,
        FeeLimitOrder REAL,
        Balance_Total REAL,
        Orders_In_Progress REAL,
        KASPA_In_Orders REAL,
        Currency_for_Trading REAL
    );
    """


drop_table_query = """
    DROP TABLE IF EXISTS orders_btcusdc;
"""



async def main():
    await db_async.connect()
    await db_async.execute(create_table_query)
    await db_async.disconnect()

asyncio.run(main())
