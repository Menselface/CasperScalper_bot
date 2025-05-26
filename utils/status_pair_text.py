from utils.additional_methods import user_active_pair, format_symbol


async def set_status_pair_text(user_id, pair):
    is_user_trade_now = await user_active_pair(user_id, pair)
    result_text_pair = format_symbol(pair)
    if is_user_trade_now:
        return f"{result_text_pair} ✅"
    return result_text_pair
