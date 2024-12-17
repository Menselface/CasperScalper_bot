# price.py
import requests
import datetime

# Функция для получения курсов валют
async def handle_price(message):
    user_id = message.from_user.id

    urls = {
        "KASPA": 'https://api.mexc.com/api/v3/ticker/price?symbol=KASUSDT',
        "BTC": 'https://api.mexc.com/api/v3/ticker/price?symbol=BTCUSDT',
        "SUI": 'https://api.mexc.com/api/v3/ticker/price?symbol=SUIUSDT',
        "PYTH": 'https://api.mexc.com/api/v3/ticker/price?symbol=PYTHUSDT',
        "DOT": 'https://api.mexc.com/api/v3/ticker/price?symbol=DOTUSDT'
    }

    # Отправляем запросы к API и получаем курсы
    prices = {}
    for name, url in urls.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            price = float(data['price'])
            # Форматируем курс в зависимости от монеты
            if name == "KASPA":
                prices[name] = f"{price:,.6f}"
            elif name == "BTC":
                prices[name] = f"{price:,.2f}"
            elif name == "PYTH" or name == "SUI":
                prices[name] = f"{price:,.4f}"
            elif name == "DOT":
                prices[name] = f"{price:,.3f}"
        except Exception as e:
            prices[name] = "N/A"

    # Получаем текущую дату и время
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    current_date = datetime.datetime.now().strftime('%d.%m.%Y')

    # Формируем сообщение с курсами
    message_text = (
        f"MEXC курс на {current_date}\n\n"
        f"<b>KASPA</b> - {prices['KASPA']}\n\n"
        f"<b>BTC</b> - {prices['BTC']}\n\n"
        f"<b>SUI</b> - {prices['SUI']}\n\n"
        f"<b>PYTH</b> - {prices['PYTH']}\n\n"
        f"<b>DOT</b> - {prices['DOT']}"
    )

    # Отправляем сообщение пользователю с парсингом HTML
    await message.answer(message_text, parse_mode='HTML')
