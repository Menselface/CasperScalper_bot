
import os

from db_pack.DataBaseAsync import *
from dotenv import load_dotenv
load_dotenv()

# Токен бота Telegram
TOKEN = os.getenv('TOKEN')

BASE_URL = os.getenv("BASE_URL")

# сюда добавить адрес базы данных сервера 128 (а на 116 другой адрес)
"""Основной первый сервер 128 """
db_async = DatabaseAsync(os.getenv("DB_ASYNC"))

"""Второй сервер  116 """
# db_async = DatabaseAsync(os.getenv("DB_ASYNC2"))

# Берутся ID - для отправки админам сообщения о регистрации

ADMIN_ID = os.getenv("ADMIN_ID")
ADMIN_ID2 = os.getenv("ADMIN_ID2")

"""Добавил строгие таблицы для динамических запросов от SQL Injections"""
PAIR_TABLE_MAP = {
    "KASUSDT": "orders",
    "BTCUSDC": "orders_btcusdc",
    "SUIUSDT": "sui_usdt_orders",
    "TAOUSDT": 'tao_usdt_orders',
    "PYTHUSDT": "pyth_usdt_orders",
    "DOTUSDT": "orders_dot_usdt"
}
