from balance.balance import get_order_data
from trading.db_querys.db_symbols_for_trade_methods import get_user_symbol_data


async def get_user_buy_sum(user_id, symbol):
    result = await get_order_data(user_id, symbol)
    return round(result['buy_sum'], 2)