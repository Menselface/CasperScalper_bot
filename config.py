import os

from dotenv import load_dotenv

from DataBaseAsync import *

load_dotenv()
""" ----------------------------- DEFAULT CONFIG ------------------------------------ """
TOKEN = os.getenv("TOKEN")
db_async = DatabaseAsync(os.getenv("DB_ASYNC"))
BASE_URL = os.getenv("BASE_URL")
ADMIN_ID = os.getenv("ADMIN_ID")

PAIR_TABLE_MAP = {
    "KASUSDT": "orders",
    "BTCUSDC": "orders_btcusdc",
    "SUIUSDT": "sui_usdt_orders",
    "PYTHUSDT": "pyth_usdt_orders",
    "DOTUSDT": "orders_dot_usdt"
}
