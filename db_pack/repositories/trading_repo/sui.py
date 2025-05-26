from db_pack import BaseRepositories
from utils.decorators import db_safe_call


class SuiRepo(BaseRepositories):
    repo = 'sui_usdt_orders'
    
    
class GetSuiTable(SuiRepo):
    ...