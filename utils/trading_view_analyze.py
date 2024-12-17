import asyncio
from datetime import datetime

from aiogram import types, Bot
import aiohttp

from tradingview_ta import Interval, TA_Handler

from config import PAIR_TABLE_MAP, ADMIN_ID
from db import get_all_id_with_registered_to_status, get_first_message


# Получаем данные по сигналу через TradingView_TA (фейковый метод)
async def handle_start(pair: str="KASUSDT") -> str:
    try:
        handler = TA_Handler(symbol=pair,
                             screener='Crypto',
                             exchange='MEXC',
                             interval=Interval.INTERVAL_1_MINUTE
                             )
        analysis = handler.get_analysis().summary
        recommendation = analysis['RECOMMENDATION']
        return recommendation
        # if "STRONG" in recommendation:
        #     if recommendation == "BUY":
        #         return "STRONG_BUY"
    except Exception as e:
        print(e)


# Получаем статистику за 24 часа
async def get_24hr_stats(pair: str) -> dict:
    url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={pair.upper()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None


# Получаем данные книги ордеров (ликвидность)
async def get_order_book(pair: str) -> dict:
    url = f"https://api.mexc.com/api/v3/depth?symbol={pair.upper()}&limit=5"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None


async def get_candlestick_data(pair: str, interval: str = "1d", limit: int = 2) -> list:
    url = "https://api.mexc.com/api/v3/klines"
    params = {
        "symbol": pair,
        "interval": interval,
        "limit": limit
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Ошибка запроса: {response.status} - {await response.text()}")
                return None



# Основная функция анализа
async def analyze_pair(pair: str):
    signal = await handle_start('PYTHUSDT')
    # if signal != "STRONG_BUY":
    #     return

    stats = await get_24hr_stats(pair)
    if not stats:
        return f"Не удалось получить статистику для пары {pair}"

    volume = float(stats["volume"])
    quote_volume = float(stats["quoteVolume"])
    last_price = float(stats["lastPrice"])
    high_price = float(stats["highPrice"])
    low_price = float(stats["lowPrice"])
    price_change_percent = float(stats["priceChangePercent"])

    # Проверяем ликвидность
    order_book = await get_order_book(pair)
    if not order_book:
        return f"Не удалось получить данные книги ордеров для {pair}"
    bids = order_book["bids"]  # Сторона покупки
    asks = order_book["asks"]  # Сторона продажи

    # Анализ тренда
    candlesticks = await get_candlestick_data(pair)
    if not candlesticks or len(candlesticks) < 2:
        return f"Не удалось получить свечи для анализа {pair}"
    prev_open_price = float(candlesticks[0][1])
    current_close_price = float(candlesticks[1][4])

    price_trend = (current_close_price - prev_open_price) / prev_open_price * 100

    # Логика принятия решения
    if volume > 1000 and price_trend > 2 and float(bids[0][1]) > float(asks[0][1]):
        return True, (
            f"Рекомендуем инвестировать в {pair}:\n"
            f"- Сигнал:{signal}\n"
            f"- Объем торгов за 24 часа: {volume} {pair[:3]}\n"
            f"- Цена сейчас: {last_price} USDT\n"
            f"- Изменение за час: {round(price_trend, 2)}%\n"
            f"- Поддержка в книге ордеров: сильная."
        )
    else:
        return False, f"{pair}: Условия для покупки не удовлетворяют: низкий объем или тренд слабый."



async def handle_start_trading_view(bot: Bot):
    while True:
        for symbol in PAIR_TABLE_MAP.keys():
            result, text = await analyze_pair(symbol)
            await asyncio.sleep(5)
        
            if result:
                user_id = ADMIN_ID
                await bot.send_message(user_id, text)
        await asyncio.sleep(3600)
        