import asyncio
from typing import List

from db_pack import BaseRepositories
from utils.decorators import db_safe_call

class SymbolsForTradeRepo(BaseRepositories):
    repo = 'symbols_for_trade'

class GetSymbolForTradeRepo(SymbolsForTradeRepo):

    @db_safe_call(default_return=[])
    async def all_active_id_from_symbols_for_trade(self) -> List[int]:
        await self.connection_pool()
        result = await self.pool.fetch(
            'SELECT DISTINCT telegram_id FROM symbols_for_trade WHERE start_stop IS true ORDER BY telegram_id')
        return [record['telegram_id'] for record in result]

    @db_safe_call(default_return=[])
    async def select_for_parameters_keyboard(self, user_id: int, symbol_name: str):
        await self.connection_pool()
        result = await self.pool.fetchrow(
            "SELECT order_limit_by, percent_profit, auto_buy_down_perc FROM symbols_for_trade WHERE telegram_id = $1 AND symbol_name = $2", user_id, symbol_name
        )
        return result

    @db_safe_call(default_return=[])
    async def get_users_with_active_symbols(self):
        await self.connection_pool()
        query = ("""
                    SELECT telegram_id, array_agg(symbol_name ORDER BY symbol_name) AS symbols
                    FROM symbols_for_trade
                    WHERE start_stop = true
                    GROUP BY telegram_id
                    ORDER BY telegram_id;

                """)
        rows = await self.pool.fetch(query)
        return {user_id: symbols for user_id, symbols in rows}



class DeleteFromSymbolsForTrade(BaseRepositories):
    @db_safe_call(default_return=[])
    async def delete_user_if_not_in_user_table(self, user_id):
        result = await self.pool.fetch("""DELETE FROM symbols_for_trade WHERE telegram_id = $1""",
                                      user_id)
