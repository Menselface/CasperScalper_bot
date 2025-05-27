import asyncio
import random

from loguru import logger

from services.mexc_api.all_mexc_methods.AccountMexc import AccountMexcMethods
from infrastructure.db_pack.db import get_secret_key, get_access_key


async def validation_user_keys(user_id):
    user_api_keys = await get_access_key(user_id)
    user_secret_key = await get_secret_key(user_id)
    mexc = AccountMexcMethods(user_api_keys, user_secret_key)
    retries = random.randint(5, 9)
    delay = random.randint(2, 10)

    for attempt in range(1, retries + 1):
        try:
            res = await mexc.get_account_info_()

            logger.debug(f"Attempt {attempt}: Response from API: {res}")

            if not res:
                logger.warning(f"Attempt {attempt}: Empty response or None from API")
            else:
                if res.get("msg") == "Signature for this request is not valid.":
                    return False
                if res.get("msg") == "Api key info invalid":
                    return False
                # if "not in the ip white list" in res.get("msg"):
                #     logger.warning(f"Пользователь {user_id} Ошибка блока по айпи\n {res.get('msg')}")
                #     return False
                return True

        except Exception as e:
            logger.error(f"Attempt {attempt}: Error in validation_user_keys: {e}")

        if attempt < retries:
            logger.info(f"Retrying in {delay} seconds... ({attempt}/{retries})")
            await asyncio.sleep(delay)

    logger.critical(f"All {retries} attempts failed. Returning False.")
    return False
