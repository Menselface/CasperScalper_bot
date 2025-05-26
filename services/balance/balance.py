from services.mexc_api.all_mexc_methods.AccountMexc import AccountMexcMethods
from db_pack.db import get_access_key, get_secret_key, \
    get_all_open_sell_orders_autobuy_from_any_table_for_checker
from trading.buy_sell_methods.buy_sell import get_symbol_price
from trading.db_querys.db_symbols_for_trade_methods import get_user_symbol_data


class AssetBalance:
    def __init__(self, symbol: str, symbol_for_text: str, available: float, in_orders: float, orders_count: int = 0,
                 buy_sum: float = 0.0, sell_sum: float = 0.0, limit: float = 0.0, for_total = 0.0):
        self.symbol = symbol
        self.available = available
        self.in_orders = in_orders
        self.orders_count = orders_count
        self.buy_sum = buy_sum
        self.sell_sum = sell_sum
        self.limit = limit
        self.for_total = for_total
        self.symbol_for_text = symbol_for_text
    
    def to_text(self, user_id) -> str:
        """Форматирование текста для вывода баланса."""
        base_text = (
            f"<b>{self.symbol_for_text}</b>\n"
            f"Доступно: {self.format_for_available()}\n"
            f"В ордерах: {self.format_in_orders()}\n"
        )
        
        if self.orders_count > 0 or self.buy_sum > 0 or self.sell_sum > 0 or self.limit > 0:
            currency = "USDC" if self.symbol == "BTC" else "USDT"
            base_text += (
                f"Кол-во ордеров: {self.orders_count}\n"
                f"Лимит: {self.format_for_limit()} {currency}\n"
                f"Сумма в ордерах покупки: {self.buy_sum:.2f} {currency}\n"
                f"Сумма в ордерах продажи: {self.sell_sum:.2f} {currency}\n"
            )
        
        return base_text
    
    def format_in_orders(self):
        return f"{self.in_orders:.6f}" if self.symbol == "BTC" else f"{self.in_orders:.2f}"
    
    def format_for_available(self):
        return f"{self.available: .6f}" if self.symbol == "BTC" else f"{self.available:.2f}"
    
    def format_for_limit(self):
        return f"♾️" if self.limit == 1000000 else f"{self.limit}"


async def get_balance_data(user_id: int) -> dict:
    """Получает данные о балансе пользователя с биржи."""
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    acc_info = AccountMexcMethods(user_api_keys, user_secret_key)
    await acc_info.get_account_info_()
    return {
        "usdt": {"available": acc_info.total_free_usdt, "in_orders": acc_info.usdt_locked},
        "usdc": {"available": acc_info.total_free_usdc, "in_orders": acc_info.usdc_locked},
        "kaspa": {"available": acc_info.free_kas, "in_orders": acc_info.locked, "for_total" : acc_info.free_kas * await get_symbol_price("KASUSDT")},
        "btc": {"available": acc_info.free_btc, "in_orders": acc_info.locked_btc, "for_total" : acc_info.free_btc * await get_symbol_price("BTCUSDC")},
        "sui": {"available": acc_info.free_sui, "in_orders": acc_info.locked_sui, "for_total" : acc_info.free_sui * await get_symbol_price("SUIUSDT")},
        "tao": {"available": acc_info.free_tao, "in_orders": acc_info.locked_tao, "for_total": acc_info.free_tao * await get_symbol_price("TAOUSDT")},
        "pyth": {"available": acc_info.free_pyth, "in_orders": acc_info.locked_pyth, "for_total" : acc_info.free_pyth * await get_symbol_price("PYTHUSDT")},
        "dot": {"available": acc_info.free_dot, "in_orders": acc_info.locked_dot, "for_total" : acc_info.free_dot * await get_symbol_price("DOTUSDT")}
    }

async def get_order_data(user_id: int, symbol: str) -> dict:
    """Получает данные по ордерам для заданной валюты/пары."""
    
    all_orders = await get_all_open_sell_orders_autobuy_from_any_table_for_checker(user_id, symbol)
    limit = await get_user_symbol_data(user_id, symbol, "trade_limit")
    buy_sum = sum(order['totalamountonpurchace'] for order in all_orders)
    sell_sum = sum((order['priceordersell'] or 0) * (order['qtytosell'] or 0) for order in all_orders)
    return {
        "count": len(all_orders),
        "buy_sum": buy_sum,
        "sell_sum": sell_sum,
        "limit": limit
    }
