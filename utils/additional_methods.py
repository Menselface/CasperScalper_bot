import asyncio
import datetime

import pytz

from db import get_all_open_sell_orders
from all_mexc_methods.mexc_methods import CreateSpotConn
from db import get_secret_key, get_access_key
from db import get_all_open_sell_orders_autobuy


class AutoBuy:
    def __init__(self):
        self.is_working = False
        self.websocket_work = False
        self.user_autobuy_status = set()
        self.double_user = {}
    
    def checker(self):
        return self.is_working
    
    def checker_of_websockets(self):
        return self.websocket_work
    
    def add_user_session(self, user_id):
        if user_id not in self.user_autobuy_status:
            self.user_autobuy_status.add(user_id)
            print(self.user_autobuy_status)
    
    def remove_user(self, user_id):
        self.user_autobuy_status.discard(user_id)
        
    def user_real_autobuy_checker(self, user_id):
        if user_id in self.user_autobuy_status:
            return True
        return False


async def check_user_last_autobuy_for_reset(user_id):
    all_data_from_db = await get_all_open_sell_orders_autobuy(user_id, 1)
    sorted_records = sorted(all_data_from_db, key=lambda x: x['transacttimebuy'], reverse=True)
    print(sorted_records[0])


async def sell_orders_checker(user_id: int, actual: str):
    # actual = 'C02__454843825987276800037'
    res = await get_all_open_sell_orders(int(user_id), actual)
    for result in res:
        if result[0] == actual:
            # print(result[0])
            return result[0]


async def get_user_commission(user_id):
    user_id = int(user_id)
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    
    res = CreateSpotConn(user_api_keys, user_secret_key)
    info = res.get_account_info_()
    commission = info.get('takerCommission')
    if not commission:
        commission = 0
    return commission


async def create_time(time):
    time = int(time)
    time_of_order_buy = time / 1000
    kyiv_tz = pytz.timezone('Europe/Kyiv')
    result = datetime.datetime.fromtimestamp(time_of_order_buy, tz=kyiv_tz)
    result_naive = result.replace(tzinfo=None)
    return result_naive


async def check_autobuy(user_id, selected_id):
    user_id = int(user_id)
    orders = await get_all_open_sell_orders_autobuy(user_id, 1)
    orders_9 = await get_all_open_sell_orders_autobuy(user_id, 9)
    orders.extend(orders_9)
    result = None
    if not orders:
        return False
    for row in orders:
        if row['order_id_limit'] == selected_id:
            result = row['order_id_limit']
    if result:
        print('True')
        return True
    return False

async def update_result_if_have_order_autobuy(user_id):
    all_data_from_db = await get_all_open_sell_orders_autobuy(user_id, 1)
    sorted_records = sorted(all_data_from_db, key=lambda x: x['transacttimebuy'], reverse=True)
    result = {'actual_order': None, 'avg_price': None}
    if len(sorted_records) > 0:
        sorted_records = sorted_records[0]
        print(result)
        result.update({'actual_order': sorted_records['order_id_limit'], 'avg_price': sorted_records['priceorderbuy']})
    return result


async def remove_user_from_is_working_status(user_id, is_working):
    is_working.is_working = False
    is_working.remove_user(user_id)
