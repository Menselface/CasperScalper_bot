import asyncio

from DataBaseAsync import *


create_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,  -- просто номер по порядку
        telegram_id BIGINT UNIQUE NOT NULL,  -- Идентификатор пользователя в Telegram
        first_name TEXT,  -- Имя пользователя
        last_name TEXT,  -- Фамилия пользователя
        username TEXT,  -- Имя пользователя в Telegram (заполнять в виде @jamesbond)
        registered_at TIMESTAMP NOT NULL,  -- Дата и время регистрации пользователя
        api_key TEXT CHECK (length(api_key) <= 100),  -- API ключ биржи
        secret_key TEXT CHECK (length(secret_key) <= 100),  -- Секретный ключ биржи
        registered_to TIMESTAMP,  -- Дата и время, до которого пользователь зарегистрирован (вводится потом Админом вручную)
        order_limit_by REAL DEFAULT 30.0,  -- Сумма покупки в USDT
        percent_profit REAL DEFAULT 0.30,  -- Процент прибыли
        autobuy_up_sec INTEGER DEFAULT 30,  -- АвтоБай при росте (интервал автопокупки в секундах)
        auto_buy_down_perc REAL DEFAULT 1.0,  -- Процент, при котором сработает АвтоБай при падении
        commission_percent REAL DEFAULT 0.02,  -- Процент комиссии биржи
        message TEXT,  -- запасная графа
        is_admin BOOLEAN DEFAULT false,  -- запасная графа
        reset_autobuy INTEGER DEFAULT 0, -- запасная графа
        stop_buy INTEGER DEFAULT 0
    );
    """

# s = """UPDATE users
# SET reset_autobuy = 0
# WHERE reset_autobuy IS NULL;
# """


# async def main():
#     await db_async.connect()
#     await db_async.execute(create_table_query)
#     await db_async.disconnect()


# asyncio.run(main())
