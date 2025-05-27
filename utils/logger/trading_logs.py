from typing import Any



class TradingLogs:
    counter = 0
    def __init__(self, user_id: int, symbol: str):
        from utils.logger import get_user_logger
        self.logger = get_user_logger(user_id, symbol)
        self.symbol = symbol
        self.user_id = user_id

    def _log(self, text: str, is_warning: bool = False):
        if is_warning:
            self.logger.warning(text)
        else:
            self.logger.info(text)

    def limit_message(self, first=False, minute=False, symbol: str = None):
        templates = (
            f"Модуль {self.symbol} первый раз зашел в проверка лимита" if first else
            f"Модуль {self.symbol} проверка лимита каждую минуту" if minute else
            f"Не передали значения: {self.symbol}"
        )
        self._log(templates, not (first or minute))

    def balance_message(self, first=False, minute=False, symbol: str = None):
        templates = (
            f"Модуль {self.symbol} первый раз зашел в нехватку USDT" if first else
            f"Модуль {self.symbol} проверка нехватки баланса каждую минуту" if minute else
            f"Не передали значения: {self.symbol}"
        )
        self._log(templates, not (first or minute))

    def user_expired_and_stop(self):
        text = "Модуль остановлен для пользователя - Закончилась подписка"
        self._log(text)

    def user_automatically_reset(self, order_id: str):
        text = f"У пользователя есть открытый ордер, взял данные из колбасы  - {order_id}"
        self._log(text)

    def open_new_order(self):
        text = 'Открываем новый ордер'
        self._log(text)

    def order_limits_by_and_trade_limit_user(self, order_limit: int, trade_limit):
        text = f"""Установлены лимиты для пользователя:
        • Цена ордеров: {order_limit}
        • Торговый лимит: {trade_limit}"""
        self._log(text)

    def critical_error_after_buying(self, limit: bool = False):
        text = ("Торговля остановлена: критическая ошибка после выставления лимитной покупки" if limit else
        "Торговля остановлена: критическая ошибка после покупки")
        self._log(text, is_warning=True)

    def all_limits_messages_reset_to_zero(self):
        text = "Все флаги лимитов сброшены пользователю на 0 в таблице symbols_for_trade"
        self._log(text)

    def return_open_orders_dict_data(self, dict_data):
        text = f'Данные которые вернулись после открытия ордера {dict_data}'
        self._log(text)

    def open_limit_order_result(self, result: dict[str, Any]):
        text = f"Данные которые вернулись после попытки открыть лимитный ордер {result}"
        self._log(text)

    def get_all_data_in_while_trading_module(self, data: dict[str, Any]):
        if self.is_counter_zero():
            text = f"Текущая цена: {data['sui_price']:.4f}"
        else:
            text = f"""┌ Торговые параметры {data['symbol_name']}
        │ Текущая цена: {data['sui_price']:.4f}
        │ Автодокупка: {data['auto_buy_down_perc']}% | Прибыль: {data['percent_profit']}%
        ├───────────────────
        │ Sell Target: {data['sold_price']:.4f}
        └ Buy Trigger: {data['threshold_price']:.4f}"""
        self.set_counter()
        self._log(text)

    def trading_was_stop_by_user(self):
        text = "Модуль SUI/USDT остановлен пользователем !"
        self._log(text)

    def autobuy_was_closed(self, actual_order_id: str, overprice: bool = False):
        text = (f"Ордер был закрыт через проверку автобай, номер - {actual_order_id}" if not overprice else
                f"Цена выше предпологаемой, выходим из цикла проверки, ордер номер - {actual_order_id}")
        self._log(text)

    def price_is_above_threshold(self, threshold_price):
        self._log(f"Цена упала до {threshold_price}, выходим из цикла проверки")

    @classmethod
    def is_counter_zero(cls):
        if cls.counter == 0:
            return False
        return True

    @classmethod
    def set_counter(cls):
        cls.counter += 1
        if cls.counter == 100:
            cls.set_counter_to_zero()

    @classmethod
    def set_counter_to_zero(cls):
        cls.counter = 0
