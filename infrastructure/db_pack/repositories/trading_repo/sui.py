from infrastructure.db_pack import BaseRepositories


class SuiRepo(BaseRepositories):
    repo = "sui_usdt_orders"


class GetSuiTable(SuiRepo): ...
