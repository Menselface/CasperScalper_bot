import datetime

from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_ID
from services.balance import get_balance_data, get_order_data, AssetBalance
from utils.status_pair_text import set_status_pair_text

balance_router = Router(name=__name__)


@balance_router.message(Command("balance"))
async def handle_balance(message: Message, bot: Bot):
    try:
        user_id = message.from_user.id

        balance_data = await get_balance_data(user_id)

        btc_order_data = await get_order_data(user_id, "BTCUSDC")
        kaspa_order_data = await get_order_data(user_id, "KASUSDT")
        sui_order_data = await get_order_data(user_id, "SUIUSDT")
        pyth_order_data = await get_order_data(user_id, "PYTHUSDT")
        dot_order_data = await get_order_data(user_id, "DOTUSDT")
        tao_order_data = await get_order_data(user_id, "TAOUSDT")

        balances = [
            AssetBalance(
                "USDT",
                "USDT",
                balance_data.get("usdt", {}).get("available", 0),
                balance_data.get("usdt", {}).get("in_orders", 0),
            ),
            AssetBalance(
                "USDC",
                "USDC",
                balance_data.get("usdc", {}).get("available", 0),
                balance_data.get("usdc", {}).get("in_orders", 0),
            ),
            AssetBalance(
                "BTC",
                await set_status_pair_text(user_id, "BTCUSDC"),
                available=balance_data.get("btc", {}).get("available"),
                in_orders=balance_data.get("btc", {}).get("in_orders", 0),
                for_total=btc_order_data.get("btc", {}).get("for_total", 0),
                orders_count=btc_order_data.get("count", 0),
                buy_sum=btc_order_data.get("buy_sum", 0),
                sell_sum=btc_order_data.get("sell_sum", 0),
                limit=btc_order_data.get("limit", 0),
            ),
            AssetBalance(
                "KAS",
                await set_status_pair_text(user_id, "KASUSDT"),
                available=balance_data.get("kaspa", {}).get("available", 0),
                in_orders=balance_data.get("kaspa", {}).get("in_orders", 0),
                for_total=balance_data.get("kaspa", {}).get("for_total", 0),
                orders_count=kaspa_order_data.get("count", 0),
                buy_sum=kaspa_order_data.get("buy_sum", 0),
                sell_sum=kaspa_order_data.get("sell_sum", 0),
                limit=kaspa_order_data.get("limit", 0),
            ),
            AssetBalance(
                "SUI",
                await set_status_pair_text(user_id, "SUIUSDT"),
                available=balance_data.get("sui", {}).get("available", 0),
                in_orders=balance_data.get("sui", {}).get("in_orders", 0),
                for_total=balance_data.get("sui", {}).get("for_total", 0),
                orders_count=sui_order_data.get("count", 0),
                buy_sum=sui_order_data.get("buy_sum", 0),
                sell_sum=sui_order_data.get("sell_sum", 0),
                limit=sui_order_data.get("limit", 0),
            ),
            AssetBalance(
                "TAO",
                await set_status_pair_text(user_id, "TAOUSDT"),
                available=balance_data.get("tao", {}).get("available", 0),
                in_orders=balance_data.get("tao", {}).get("in_orders", 0),
                for_total=balance_data.get("tao", {}).get("for_total", 0),
                orders_count=tao_order_data.get("count", 0),
                buy_sum=tao_order_data.get("buy_sum", 0),
                sell_sum=tao_order_data.get("sell_sum", 0),
                limit=tao_order_data.get("limit", 0),
            ),
            AssetBalance(
                "PYTH",
                await set_status_pair_text(user_id, "PYTHUSDT"),
                available=balance_data.get("pyth", {}).get("available", 0),
                in_orders=balance_data.get("pyth", {}).get("in_orders", 0),
                for_total=balance_data.get("pyth", {}).get("for_total", 0),
                orders_count=pyth_order_data.get("count", 0),
                buy_sum=pyth_order_data.get("buy_sum", 0),
                sell_sum=pyth_order_data.get("sell_sum", 0),
                limit=pyth_order_data.get("limit", 0),
            ),
            AssetBalance(
                "DOT",
                await set_status_pair_text(user_id, "DOTUSDT"),
                available=balance_data.get("dot", {}).get("available", 0),
                in_orders=balance_data.get("dot", {}).get("in_orders", 0),
                for_total=balance_data.get("dot", {}).get("for_total", 0),
                orders_count=dot_order_data.get("count", 0),
                buy_sum=dot_order_data.get("buy_sum", 0),
                sell_sum=dot_order_data.get("sell_sum", 0),
                limit=dot_order_data.get("limit", 0),
            ),
        ]

        current_date = datetime.datetime.now().strftime("%d.%m.%Y")
        header = f"<b>БАЛАНС</b> {current_date}\n\n"
        total_balance_text = "\n".join(balance.to_text(user_id) for balance in balances)
        total_usd_balances = sum(
            balance.available
            for balance in balances
            if balance.symbol in ["USDT", "USDC"]
        )
        total_else_balances = sum(
            balance.for_total
            for balance in balances
            if balance.symbol not in ["USDT", "USDC"]
        )

        summary = (
            f"\n<b>Итого:</b>\n"
            f"<b>В ордерах:</b> {sum(balance.buy_sum for balance in balances):.2f} USD\n"
            f"<b>После продажи:</b> {total_usd_balances + total_else_balances + (sum(balance.sell_sum for balance in balances)):.2f} USD"
        )

        final_message = header + total_balance_text + summary
        await bot.send_message(user_id, final_message)
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"Ошибка при выведении баланса {e}")
