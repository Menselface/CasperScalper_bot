import asyncio

from config import PAIR_TABLE_MAP
from db_pack.repositories.symbols_for_trade import GetSymbolForTradeRepo


class Parameters: ...


class ParametersUtils(Parameters): ...


class ParametersCreateKeyboard(ParametersUtils):
    @staticmethod
    def format_symbol_for_keyboards(symbol: str) -> str | None:
        for quote in ["USDT", "USDC"]:
            if symbol.endswith(quote):
                base = symbol[: -len(quote)]
                return f"{base}/{quote}"

    @staticmethod
    def format_symbols_for_callbacks(symbol: str):
        return f"symbol_{symbol}"

    @staticmethod
    def format_number(value, precision=2):
        try:
            number = float(value)
            if number.is_integer():
                return str(int(number))
            return f"{round(number, precision):.{precision}f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            return str(value)

    async def get_user_parameters(self, user_id: int, symbol: str):
        user_parameters = await GetSymbolForTradeRepo().select_for_parameters_keyboard(
            user_id, symbol
        )
        the_name = self.format_symbol_for_keyboards(symbol)
        return (
            f"{the_name} - "
            f"{self.format_number(user_parameters['order_limit_by'])} | "
            f"+{self.format_number(user_parameters['percent_profit'])} | "
            f"↓{self.format_number(user_parameters['auto_buy_down_perc'])}"
        )

    async def get_symbols_for_main_keyboard(self, user_id: int):
        return [
            (
                await self.get_user_parameters(user_id, symbol),
                self.format_symbols_for_callbacks(symbol),
            )
            for symbol in PAIR_TABLE_MAP.keys()
        ]
