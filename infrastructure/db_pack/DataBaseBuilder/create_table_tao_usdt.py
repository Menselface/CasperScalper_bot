import asyncio

from loguru import logger

from config import db_async

create_table_query = """
    CREATE TABLE IF NOT EXISTS tao_usdt_orders (
        id SERIAL PRIMARY KEY,  -- просто номер по порядку
        telegram_id_Market BIGINT NOT NULL,  -- Идентификатор пользователя в Telegram
        order_id TEXT UNIQUE,
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
    )"""



async def main():
    await db_async.connect()
    await db_async.execute(create_table_query)
    logger.info('table create')
    await db_async.disconnect()

asyncio.run(main())
