from loguru import logger

from config import PAIR_TABLE_MAP
from infrastructure.db_pack import BaseRepositories
from utils.decorators import db_safe_call


class AnyTableRepo(BaseRepositories):

    @staticmethod
    async def get_pair_repo_name(repo: str):
        table_name = PAIR_TABLE_MAP.get(repo)
        if not table_name:
            raise ValueError(f"Unsupported pair: {repo}")
        return table_name


class GetOrdersAnyTable(AnyTableRepo):

    @db_safe_call(default_return=[])
    async def select_id_limit_details_of_order(
        self, repo: str, order_id_limit: str, user_id: int
    ):
        table_name = await self.get_pair_repo_name(repo)
        await self.connection_pool()
        query = f"SELECT * FROM {table_name} WHERE telegram_id_market = $1 AND order_id_limit = $2"
        res = await self.pool.fetchrow(query, user_id, order_id_limit)
        return res

    @db_safe_call(default_return=[])
    async def limit_order_id_by_order_id(self, repo: str, order_id: str, user_id: int):
        table_name = await self.get_pair_repo_name(repo)
        await self.connection_pool()
        query = f"SELECT order_id FROM {table_name} WHERE telegram_id_market = $1 AND order_id_limit = $2"
        res = await self.pool.fetchval(query, user_id, order_id)
        return res


class UpdateOrdersAnyTable(AnyTableRepo):
    @db_safe_call(default_return=[])
    async def update_order_after_sale_by_order_id_limit(
        self,
        repo: str,
        user_id: int,
        order_id: str,
        time_of_order_sell: str,
        qnty_for_sell: float,
        price_to_sell: float,
        order_id_limit: str,
        autobuy: int,
        total_amount_after_sale: float,
        feelimit: float,
        balance_total: float,
        orders_in_progress: int,
        symbol_in_orders: float,
        currency_for_trading: float,
    ):
        table_name = await self.get_pair_repo_name(repo)
        await self.connection_pool()

        query = f"""
        UPDATE {table_name}
        SET
            transacttimesell = $1,
            qtytosell = $2,
            priceordersell = $3,
            autobay = $4,
            totalamountaftersale = $5,
            feelimitorder = $6,
            balance_total = $7,
            orders_in_progress = $8,
            kaspa_in_orders = $9,
            currency_for_trading = $10
        WHERE
            telegram_id_market = $11 AND order_id_limit = $12
        """
        result = await self.pool.execute(
            query,
            time_of_order_sell,
            qnty_for_sell,
            price_to_sell,
            autobuy,
            total_amount_after_sale,
            feelimit,
            balance_total,
            orders_in_progress,
            symbol_in_orders,
            currency_for_trading,
            user_id,
            order_id_limit,
        )
        logger.debug(f"[DB] Update result: {result}")
