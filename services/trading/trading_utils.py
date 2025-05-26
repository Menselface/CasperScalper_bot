from trading.db_querys.db_symbols_for_trade_methods import update_user_symbol_data, get_user_symbol_data


class TradingService:
    def __init__(self, symbol):
        self.symbol_name = symbol


class TradeUtils(TradingService):

    async def reset_user_info_usdt_and_limit_message(self, user_id):
        await update_user_symbol_data(user_id, self.symbol_name, info_no_usdt=0)
        await update_user_symbol_data(user_id, self.symbol_name, limit_message=0)


    async def check_error_for_sleep_and_restart(self, user_id: int, error_string: str):
        list_for_restart = ["Error 429", "not_money", "Error 400"]
        if error_string == 'not_money':
            await update_user_symbol_data(user_id, self.symbol_name, info_no_usdt=1)
        if error_string in list_for_restart:
            return True
        return False

    async def if_not_start_stop_at_symbols_for_trade(self, user_id: int, manager, log):
        start_or_stop = await get_user_symbol_data(user_id, self.symbol_name, "start_stop")
        if not start_or_stop:
            await update_user_symbol_data(user_id, self.symbol_name, start_stop=False)
            await self.reset_user_info_usdt_and_limit_message(user_id)
            manager.delete_user(user_id)
            log.trading_was_stop_by_user()
            return True
        return False

    async def check_limit_message(self, user_id: int):
        return await get_user_symbol_data(user_id, self.symbol_name, "limit_message")

    async def check_balance_message(self, user_id: int):
        return await get_user_symbol_data(user_id, self.symbol_name, "info_no_usdt")

    async def check_message_status_limit_or_balance_for_user(self, user_id: int):
        limit_message = await self.check_limit_message(user_id)
        balance_message = await self.check_balance_message(user_id)
        if limit_message or balance_message:
            return True
        return False