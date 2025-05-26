from datetime import datetime, timedelta

from aiogram import Bot

from db_pack.db import status_of_ending_of_registration


async def final_of_registration_date(bot: Bot):
    months_translation = {
        'January': 'Января',
        'February': 'Февраля',
        'March': 'Марта',
        'April': 'Апреля',
        'May': 'Мая',
        'June': 'Июня',
        'July': 'Июля',
        'August': 'Августа',
        'September': 'Сентября',
        'October': 'Октября',
        'November': 'Ноября',
        'December': 'Декабря'
    }

    today = datetime.today().date()
    thresholds = {
        'three_days_before': today + timedelta(days=3),
        'one_day_before': today + timedelta(days=1),
        'today': today,
        'one_day_after': today - timedelta(days=1),
        'three_day_after': today - timedelta(days=3),
        'seven_day_after': today - timedelta(days=7)
    }

    messages = {
        'three_days_before': 'Привет! Твоя подписка на Бота подходит к концу через 3 дня. Успей продлить подписку и продолжай зарабатывать!',
        'one_day_before': 'Завтра {date} в {time} твоя подписка на Бота заканчивается! Чтобы продолжать зарабатывать, продли подписку!',
        'today': 'Сегодня {date} в {time} твоя подписка на Бота заканчивается! Чтобы продолжать зарабатывать, продли подписку!',
        'one_day_after': 'Твоя подписка на Бота завершена. Пока бот закрывает старые сделки, ты еще можешь продлить подписку и вернуться к активной торговле без потерь. Через 7 дней все сделки будут удалены.',
        'three_day_after': 'Твоя подписка на Бота завершена; через 4 дня бот остановится. Все сделки и данные будут удалены. Не теряй шанс — вернись в строй!',
        'seven_day_after': 'Остался последний день до полной остановки бота и удаления всех данных. Ты еще можешь продлить подписку и сохранить результаты. Не упусти прибыль!'
    }

    all_users = await status_of_ending_of_registration(thresholds['three_days_before'], thresholds['seven_day_after'])
    for user in all_users:
        user_id = user['telegram_id']
        reg_date = user['registered_to'].date()
        for key, threshold_date in thresholds.items():
            if reg_date == threshold_date:
                if key in ['one_day_before', 'today']:
                    reg_dt = user['registered_to']
                    date_str = reg_dt.strftime('%d %B %Y')
                    english_month = reg_dt.strftime('%B')
                    date_str = date_str.replace(english_month, months_translation.get(english_month, english_month))
                    time_str = reg_dt.strftime('%H:%M')
                    text = messages[key].format(date=date_str, time=time_str)
                else:
                    text = messages[key]
                text += f'\nРегистрация до: {user["registered_to"]}'
                await bot.send_message(chat_id=user_id, text=text)
                break
