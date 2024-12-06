import asyncio
import time
from datetime import datetime
from pprint import pprint

from aiogram import Bot
from aiogram.types import Message
from aiohttp.web_routedef import static
from loguru import logger

from all_mexc_methods.AccountMexc import AccountMexcMethods
from config import PAIR_TABLE_MAP
from db import get_all_open_sell_orders_autobuy_from_any_table, get_access_key, get_secret_key, \
    update_order_after_sale_by_order_id_any_table, get_info_commission_percent, \
    get_totalamountonpurchace_from_any_table, get_order_id_limit_from_any_table, get_all_id_with_registered_to_status, \
    get_first_message, get_all_open_sell_orders_autobuy_from_any_table_for_checker, \
    delete_order_by_user_and_order_id_from_any_table, delete_order_by_user_and_order_id_from_any_table_for_one_only_case
from utils.additional_methods import create_time, safe_format, user_message_returner


class OrdersChecker:
    def __init__(self):
        self.mexc = None
        self.user = None
        self.api_key = None
        self.api_secret = None
        
    async def user_authorization(self, user_id):
        api_key = await get_access_key(user_id)
        api_secret = await get_secret_key(user_id)
        self.mexc = AccountMexcMethods(api_key, api_secret)
        self.user = user_id
        self.api_key = api_key
        self.api_secret = api_secret
    
    async def get_asset_balance(self, account_info, pair, slice_, object_: str = "free"):
        target_asset = pair[slice_]
        for balance in account_info.get("balances", []):
            if balance["asset"] == target_asset:
                return float(balance[object_])
        return 0.0
    
    async def processing_not_found(self, not_founds):
        result = {}
        for pair, orders_list in not_founds.items():
            table_name = PAIR_TABLE_MAP.get(pair)
            if pair not in result:
                result[pair] = []
            
            for record in orders_list:
                try:
                    order = await self.mexc.get_order_status(order_id=record['order_id_limit'], symbol=pair)
                    if order == "Order lost in the echo":
                        raise Exception("Order lost in the echo")
                    status = order.get('status')
                    if status == 'FILLED':
                        result[pair].append(order)
                        logger.info(f"Данные о закрытом ордере {order}")
                    
                    if status == 'CANCELED':
                        await delete_order_by_user_and_order_id_from_any_table(table_name, self.user, order)
                        logger.info(f"canceled order deleted {order}")
                
                except Exception as e:
                    error_message = str(e)
                    if "Order lost in the echo" in error_message:
                        logger.info(f"Ордер попал в исключение - Удаляем и концы в воду.{record} \n{e}")
                        await delete_order_by_user_and_order_id_from_any_table(table_name, self.user, record['order_id'])
                        continue
                    else:
                        logger.warning(f"Ошибка при обработке ордера: {record} - {e}")
                    continue
        
        return result
    
    async def get_orders_from_exchange(self, user_id, start_time, end_time=None):
        all_data = {}
        
        for pair in PAIR_TABLE_MAP.keys():
            self.mexc.symbol = pair
            
            orders = await self.mexc.get_all_orders(start_time=start_time, end_time=end_time)
            
            if orders is not None:
                active_orders = [order for order in orders]
                all_data[pair] = active_orders
            else:
                all_data[pair] = []
        
        return all_data
    
    async def compare_orders(self, all_data, orders_from_exchange):
        result = {}
        not_found = {}
        for pair, local_orders in all_data.items():
            exchange_orders = orders_from_exchange.get(pair, [])
            result[pair] = []
            not_found[pair] = []
            
            logger.info(
                f"Проверяем пару {pair}. Локальных ордеров: {len(local_orders)}, биржевых ордеров: {len(exchange_orders)}")
            
            for local_order in local_orders:
                local_order_id = local_order.get("order_id_limit")
                matching_order = next(
                    (order for order in exchange_orders if order.get("orderId") == local_order_id),
                    None
                )
                
                if matching_order:
                    order_status = matching_order.get("status")
                    if order_status and order_status != "NEW":
                        logger.info(f"Ордер ID {local_order_id} для пары {pair} изменил статус на {order_status}.")
                        result[pair].append(matching_order)
                else:
                    not_found[pair].append(local_order)
        return result, not_found
    
    async def filter_active_orders(self, all_data):
        filtered_data = {}
        
        for pair, local_orders in all_data.items():
            active_orders_from_exchange = await self.mexc.get_open_orders(pair)
            
            if active_orders_from_exchange == '0':
                filtered_data[pair] = local_orders
                logger.info(f"Нет открытых ордеров от биржи для пары {pair}. Оставляем локальные ордера без изменений.")
                continue
                
            exchange_orders = [
                order.get("orderId")
                for order in active_orders_from_exchange
                if order.get("symbol") == pair
            ]
            
            filtered_data[pair] = [
                local_order
                for local_order in local_orders
                if local_order.get("order_id_limit") not in exchange_orders
            ]
            
            logger.info(f"После фильтрации для пары {pair}: {len(filtered_data[pair])} ордеров осталось.")
        
        return filtered_data
    
    async def fill_orders_to_tables(self,
            user_id: int,
            orders_result: dict,
    ):
        closed_orders = {}
        
        for pair, orders in orders_result.items():
            table_name = PAIR_TABLE_MAP.get(pair)
            if not table_name:
                logger.warning(f"Таблица для пары {pair} не найдена.")
                continue
            closed_orders[pair] = []
            
            for order in orders:
                try:
                    status = order.get("status")
                    if status == "FILLED":
                        logger.info(f"Обработка закрытого ордера: {order}")
                        
                        order_buy_id = order["orderId"]
                        time_of_order_sell = await create_time(order["updateTime"])
                        qnty_for_sell = order["executedQty"]
                        price_to_sell = order["price"]
                        total_after_sale = order["origQuoteOrderQty"]
                        totalamountonpurchace = await get_totalamountonpurchace_from_any_table(table_name, order_buy_id)
                        
                        user_commission = await get_info_commission_percent(user_id)
                        fee_limit_order = (
                                (float(qnty_for_sell)  * float(price_to_sell) - float(totalamountonpurchace))
                                * (1 - float(user_commission) / 100)
                        )
                        
                        account_info = await self.mexc.get_account_info_()
                        slice_last_4 = slice(-4, None)
                        slice_first_3 = slice(0, 3)
                        total_balance_usdt = await self.get_asset_balance(account_info, pair, slice_last_4)
                        total_open_trades = len(await AccountMexcMethods(self.api_key, self.api_secret).get_open_orders()) or 0
                        btc_in_orders = await self.get_asset_balance(account_info, pair, slice_first_3, "locked")
                        total_free_usdt = await self.get_asset_balance(account_info, pair, slice_first_3, "free")
                        
                        await update_order_after_sale_by_order_id_any_table(
                            table_name=table_name,
                            user_id=user_id,
                            order_id=order_buy_id,
                            time_of_order_sell=time_of_order_sell,
                            qnty_for_sell=float(qnty_for_sell),
                            price_to_sell=float(price_to_sell),
                            order_id_limit=order.get("orderId"),
                            autobuy=2,
                            total_amount_after_sale=round(float(total_after_sale), 6),
                            feelimit=fee_limit_order,
                            balance_total=total_balance_usdt,
                            orders_in_progress=total_open_trades,
                            kaspa_in_orders=btc_in_orders,
                            currency_for_trading=total_free_usdt,
                        )
                        
                        closed_orders[pair].append(order_buy_id)
                
                except Exception as e:
                    logger.error(f"Ошибка при обработке ордера {order}: {e}")
        
        logger.info(f"Пользователю {user_id} возвращены результаты: {closed_orders}")
        
        return closed_orders
    


async def start_orders_checker(bot: Bot):
    while True:
        today = datetime.today().date()
        active_users = await get_all_id_with_registered_to_status(today)
        for user in active_users:
            message = await get_first_message(user)
            user_id = message.from_user.id
            all_data = {}
            for pair, table in PAIR_TABLE_MAP.items():
                all_data[pair] = await get_all_open_sell_orders_autobuy_from_any_table_for_checker(user_id, pair)
            if all(not orders for orders in all_data.values()):
                logger.info(f"User {user_id}: all_data пустой, пропускаем.")
                continue
            
                
        
            try:
                start_time = int((time.time() - 24 * 60 * 60) * 1000)
                mexc = OrdersChecker()
                await mexc.user_authorization(user_id)
                filtered_orders = await mexc.filter_active_orders(all_data)
            
                orders = await mexc.get_orders_from_exchange(user_id, start_time)
                result, not_found = await mexc.compare_orders(filtered_orders, orders)
                res = await mexc.fill_orders_to_tables(user_id, result)
                await send_messages_to_user(message, bot, res)
                if not_found:
                    result = await mexc.processing_not_found(not_found)
                    res = await mexc.fill_orders_to_tables(user_id, result)
                    await send_messages_to_user(message, bot, res)
                    
                
                
            except Exception as e:
                logger.info(f"User {user_id} - {e}")
                continue
        await asyncio.sleep(360)
    
    
    
async def send_messages_to_user(message: Message, bot: Bot, orders: dict):
    user_id = message.from_user.id
    for pair, orders_list in orders.items():
        table_name = PAIR_TABLE_MAP.get(pair)
        try:
            for order in orders_list:
            
                res = await get_order_id_limit_from_any_table(table_name, user_id, order)
                order_buy_id = res['order_id']
                qnty_for_sell = res['qtytosell']
                price_to_sell = res['priceordersell']
                total_after_sale = res['totalamountaftersale']
                fee_limit_order = res['feelimitorder']
                user_message = user_message_returner(
                    qnty_for_sell,
                    price_to_sell,
                    total_after_sale,
                    fee_limit_order,
                    pair
                )
                await message.answer(user_message, parse_mode="HTML").as_(bot)
                print(user_message)
                logger.info(f"Отправили сообщение {order_buy_id}")
        except Exception as e:
            logger.info(f"Ошибка при отправке сообшения {e}")

