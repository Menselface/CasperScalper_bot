import requests
import datetime

# Функция для получения курсов валют
async def handle_price(message):
    user_id = message.from_user.id
    kaspa_url = 'https://api.mexc.com/api/v3/ticker/price?symbol=KASUSDT'
    kaspa_response = requests.get(kaspa_url)
    kaspa_price_data = kaspa_response.json()
    kaspa_price = f"{float(kaspa_price_data['price']):.6f}"  # Сохраняем 6 знаков для KASPA

    # URL для получения курса KAS/USDT и BTC/USDT с биржи MEXC
    btc_url = 'https://api.mexc.com/api/v3/ticker/price?symbol=BTCUSDT'

    # Выполняем запросы к API
    btc_response = requests.get(btc_url)

    # Получаем JSON-ответы
    btc_price_data = btc_response.json()

    # Получаем текущую дату и время
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    current_date = datetime.datetime.now().strftime('%d.%m.%Y')

    # Формируем строковое представление с сохранением нулей
    btc_price = f"{float(btc_price_data['price']):,.2f}"     # Сохраняем 2 знака для BTC

    # Формируем сообщение с курсами
    message_text = (
        f"MEXC курс на {current_date}\n\n"
        f"<b>KASPA</b> - {kaspa_price}\n\n"
        f"<b>BTC</b> - {btc_price}"
    )

    # Отправляем сообщение пользователю с парсингом HTML
    await message.answer(message_text, parse_mode='HTML')
