from loguru import logger

from all_mexc_methods.AccountMexc import AccountMexcMethods


async def validation_user_keys(api_key, api_secret):
    mexc = AccountMexcMethods(api_key, api_secret)
    try:
        res = await mexc.get_account_info_()
        if res.get("msg") == "Signature for this request is not valid.":
            return False
        if res.get('msg') == 'Api key info invalid':
            return False
        else:
            return True
    except Exception as e:
        logger.critical(e)
        return False
        