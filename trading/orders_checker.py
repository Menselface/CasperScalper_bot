# import asyncio
# from datetime import datetime, timedelta
#
# from aiogram.types import Message
# from aiogram import Bot
# from loguru import logger
#
# from all_mexc_methods.AccountMexc import AccountMexcMethods
# from db import get_access_key, get_secret_key, get_registered_to_status, get_all_open_sell_orders_nine, \
#     update_orderafter_sale_by_order_id, delete_order_by_user_and_order_id, get_all_id_with_registered_to_status, \
#     get_first_message, get_info_commission_percent, get_all_open_sell_orders_nine
# from trading.buy_sell_methods.buy_sell import get_symbol_price
# from trading.db_querys.db_for_btc_table import delete_order_by_user_and_order_id_btc, get_all_open_sell_orders_nine_btc, \
#     update_orderafter_sale_by_order_id_btc
# from trading.trading_btc import send_messages_to_user_btc
# from trading.trading_kas import send_messages_to_user
# from utils.additional_methods import create_time
#
#
# async def start_orders_checker(bot: Bot):
#     today = datetime.today().date()
#     active_users = await get_all_id_with_registered_to_status(today)
#
#     tasks = []
#
#     for user in active_users:
#         res = await get_first_message(user)
#         task = asyncio.create_task(orders_checker_only_nine(res, bot))
#         task_btc = asyncio.create_task(orders_checker_only_nine_for_btc(res, bot))
#         tasks.append(task)
#         tasks.append(task_btc)
#     logger.info(f"Проверка ордеров пользователей запущенна {active_users}")
#
#     await asyncio.gather(*tasks)
#
#
# async def orders_checker_only_nine(message: Message, bot):
#     user_id = message.from_user.id
#     user_api_keys = await get_access_key(user_id)
#     user_secret_key = await get_secret_key(user_id)
#     http_mexc = AccountMexcMethods(user_api_keys, user_secret_key)
#     user_commission = await get_info_commission_percent(user_id)
#     current_price = await get_symbol_price('KASUSDT')
#     while True:
#         user_alive_status = await get_registered_to_status(user_id)
#         today = datetime.now()
#         max_alive_user = user_alive_status['registered_to'] + timedelta(days=7)
#         if today.strftime('%Y-%m-%d %H:%M') == max_alive_user.strftime('%Y-%m-%d %H:%M'):
#             logger.info(f"Конечная остановка у пользователя {user_id}")
#             return
#
#         user_orders_from_table_nine = await get_all_open_sell_orders_nine(user_id, 9, current_price)
#         closed_orders = set()
#         for record in user_orders_from_table_nine:
#             try:
#                 order = await http_mexc.get_order_status(record['order_id_limit'])
#                 status = order.get('status')
#                 if status == 'FILLED':
#
#                     totalamountonpurchace = record['totalamountonpurchace']
#                     order_buy_id = order.get('orderId')
#                     logger.info(
#                         f"Пользователь {user_id}: закрыт ордер {order_buy_id}")
#
#                     time_of_order_sell = await create_time(order.get('updateTime'))
#                     qnty_for_sell = order.get('executedQty')
#                     price_to_sell = order.get('price')
#                     total_after_sale = order.get('origQuoteOrderQty')
#                     account_info = await http_mexc.get_account_info_()
#                     fee_limit_order = (float(total_after_sale) - float(totalamountonpurchace)) * (1 - float(user_commission) / 100)
#                     total_balance_usdt = http_mexc.total_after_sale or 0
#                     total_open_trades = len(await http_mexc.get_open_orders()) or 0
#                     kaspa_in_orders = http_mexc.total_after_sale_Kass or 0
#                     total_free_usdt = http_mexc.total_free_usdt or 0
#
#                     await update_orderafter_sale_by_order_id(int(user_id), str(order_buy_id),
#                                                              time_of_order_sell,
#                                                              float(qnty_for_sell),
#                                                              float(price_to_sell),
#                                                              order_id_limit=record['order_id_limit'],
#                                                              autobuy=2,
#                                                              total_amount_after_sale=total_after_sale,
#                                                              feelimit=fee_limit_order,
#                                                              balance_total=total_balance_usdt,
#                                                              orders_in_progress=total_open_trades,
#                                                              kaspa_in_orders=kaspa_in_orders,
#                                                              currency_for_trading=total_free_usdt
#                                                              )
#                     closed_orders.add(order_buy_id)
#                 if status == 'CANCELED':
#                     await delete_order_by_user_and_order_id(user_id, record['order_id_limit'])
#                     logger.info(f"User {user_id} canceled order with status 9 {order}")
#
#
#             except Exception as e:
#                 logger.info(f"Ордер попал в исключение - {e}")
#                 await delete_order_by_user_and_order_id(user_id, record['order_id_limit'])
#                 continue
#             else:
#                 pass
#         await send_messages_to_user(message, closed_orders, bot)
#         await asyncio.sleep(20)
#
#
# async def orders_checker_only_nine_for_btc(message: Message, bot):
#     user_id = message.from_user.id
#     user_api_keys = await get_access_key(user_id)
#     user_secret_key = await get_secret_key(user_id)
#     http_mexc = AccountMexcMethods(user_api_keys, user_secret_key, symbol="BTCUSDC")
#     user_commission = await get_info_commission_percent(user_id)
#     current_price = await get_symbol_price('BTCUSDC')
#     while True:
#         user_alive_status = await get_registered_to_status(user_id)
#         today = datetime.now()
#         max_alive_user = user_alive_status['registered_to'] + timedelta(days=7)
#         if today.strftime('%Y-%m-%d %H:%M') == max_alive_user.strftime('%Y-%m-%d %H:%M'):
#             logger.info(f"Конечная остановка у пользователя {user_id}")
#             return
#
#         user_orders_from_table_nine = await get_all_open_sell_orders_nine_btc(user_id, 9, current_price)
#         closed_orders = set()
#         for record in user_orders_from_table_nine:
#             try:
#                 order = await http_mexc.get_order_status(record['order_id_limit'])
#                 status = order.get('status')
#                 if status == 'FILLED':
#                     totalamountonpurchace = record['totalamountonpurchace']
#                     order_buy_id = order.get('orderId')
#                     logger.info(
#                         f"Пользователь {user_id}: закрыт ордер {order_buy_id}")
#
#                     time_of_order_sell = await create_time(order.get('updateTime'))
#                     qnty_for_sell = order.get('executedQty')
#                     price_to_sell = order.get('price')
#                     total_after_sale = order.get('origQuoteOrderQty')
#                     account_info = await http_mexc.get_account_info_()
#                     fee_limit_order = (float(total_after_sale) - float(totalamountonpurchace)) * (1 - float(user_commission) / 100)
#                     total_balance_usdc = http_mexc.total_after_sale_usdc or 0
#                     total_open_trades = len(await http_mexc.get_open_orders()) or 0
#                     btc_in_orders = http_mexc.total_after_sale_btc or 0
#                     total_free_usdc = http_mexc.total_free_usdc or 0
#
#                     await update_orderafter_sale_by_order_id_btc(int(user_id), str(order_buy_id),
#                                                              time_of_order_sell,
#                                                              float(qnty_for_sell),
#                                                              float(price_to_sell),
#                                                              order_id_limit=record['order_id_limit'],
#                                                              autobuy=2,
#                                                              total_amount_after_sale=total_after_sale,
#                                                              feelimit=fee_limit_order,
#                                                              balance_total=total_balance_usdc,
#                                                              orders_in_progress=total_open_trades,
#                                                              kaspa_in_orders=btc_in_orders,
#                                                              currency_for_trading=total_free_usdc
#                                                              )
#                     closed_orders.add(order_buy_id)
#                 if status == 'CANCELED':
#                     await delete_order_by_user_and_order_id_btc(user_id, record['order_id_limit'])
#                     logger.info(f"User {user_id} canceled order with status 9 {order}")
#
#
#             except Exception as e:
#                 logger.info(f"Ордер попал в исключение - {e}")
#                 continue
#             else:
#                 pass
#         await send_messages_to_user_btc(message, closed_orders, bot)
#         await asyncio.sleep(20)