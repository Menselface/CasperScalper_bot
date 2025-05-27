from loguru import logger

from services.mexc_api.all_mexc_methods.AccountMexc import AccountMexcMethods
from infrastructure.db_pack import (
    get_access_key,
    get_secret_key,
    get_all_open_sell_orders_autobuy,
    delete_order_by_user_and_order_id,
)


async def global_orders_checker_for_user(user_id):
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    http_mexc = AccountMexcMethods(user_api_keys, user_secret_key)
    user_orders_from_table = await get_all_open_sell_orders_autobuy(user_id, 1)
    user_orders_from_table_nine = await get_all_open_sell_orders_autobuy(user_id, 9)
    user_orders_from_table.extend(user_orders_from_table_nine)
    for record in user_orders_from_table:
        try:
            order = await http_mexc.get_order_status(record["order_id_limit"])
            status = order.get("status")
            if status == "CANCELED":
                await delete_order_by_user_and_order_id(
                    user_id, record["order_id_limit"]
                )
                logger.info(f"User {user_id} canceled order with status 1 {order}")

        except Exception as e:
            logger.info(f"Ордер попал в исключение - {e}")
            continue
        else:
            pass
