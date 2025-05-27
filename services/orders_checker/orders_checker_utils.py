from loguru import logger

from infrastructure.db_pack.repositories.trading_repo import GetOrdersAnyTable
from services.mexc_api.get import GetMexcAPI
from utils.decorators import handle_commission_errors


class OrdersCheckerUtils: ...


class CountOrderCommission(OrdersCheckerUtils):

    def __init__(self, user_id: int, order_id: str, symbol: str):
        self.select_from_orders = GetOrdersAnyTable()
        self.user_id = user_id
        self.order_id = order_id
        self.symbol = symbol

    def _validate_commission_response(self, res: any, commission_type: str) -> float:
        error_prefix = f"{self.__class__.__name__} {commission_type}"
        if not res:
            logger.warning(f"[{error_prefix}] Empty response: {res}")
            return 0.0

        if not isinstance(res, list) or not res:
            logger.warning(f"[{error_prefix}] Invalid response format: {res}")
            return 0.0

        if "commission" not in res[0]:
            logger.warning(f"[{error_prefix}] Missing commission field: {res}")
            return 0.0

        try:
            return float(res[0]["commission"])
        except (TypeError, ValueError) as e:
            logger.warning(f"[{error_prefix}] Invalid commission value: {e}")
            return 0.0

    @handle_commission_errors(default_return=0.0)
    async def get_buyer_commission(self):
        mexc = await GetMexcAPI.create(self.user_id)
        res = await mexc.order_commission(self.symbol, self.order_id)
        return self._validate_commission_response(res, "buyer")

    @handle_commission_errors(default_return=0.0)
    async def get_maker_commission(self):
        limit_order_id = await self.select_from_orders.limit_order_id_by_order_id(
            self.symbol, self.order_id, self.user_id
        )
        if not limit_order_id:
            logger.warning(
                f"[{self.__class__.__name__} maker] No limit_order_id for {self.order_id}"
            )
            return 0.0

        mexc = await GetMexcAPI.create(self.user_id)
        res = await mexc.order_commission(self.symbol, limit_order_id)
        return self._validate_commission_response(res, "maker")

    async def maker_plus_taker_commission_result(self):
        return await self.get_maker_commission() + await self.get_buyer_commission()

    async def return_commission_total_result(self):
        return await self.maker_plus_taker_commission_result()
