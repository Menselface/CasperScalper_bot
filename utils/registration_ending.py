import asyncio
from datetime import datetime, timedelta

from aiogram import Bot
from loguru import logger

from db import status_of_ending_of_registration


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
    
    while True:
        today = datetime.today()
        three_days_before = today + timedelta(days=3)
        one_day_before = today + timedelta(days=1)
        twelve_hours_before = today + timedelta(hours=12)
        one_day_after = today - timedelta(days=1)
        three_day_after = today - timedelta(days=3)
        seven_day_after = today - timedelta(days=7)
        
        all_users = await status_of_ending_of_registration(three_days_before, seven_day_after)
        for user in all_users:
            user_id = user['telegram_id']
            user_actual_status = user['registered_to'].strftime('%Y-%m-%d %H:%M:%S')
            if user_actual_status == three_days_before.strftime('%Y-%m-%d %H:%M:%S'):
                await bot.send_message(chat_id=user_id, text=f'Привет! Твоя подписка на Бота подходит к концу через 3 дня. '
                                                             f'Успей продлить подписку и продолжай зарабатывать!\nPегистрация до {user_actual_status_}')
            if user_actual_status == one_day_before.strftime('%Y-%m-%d %H:%M:%S'):
                user_actual_status_ = user['registered_to']
                
                date = user_actual_status_.strftime('%d %B %Y')
                english_month = user_actual_status_.strftime('%B')
                date = date.replace(english_month, months_translation[english_month])
                
                time = user_actual_status_.strftime('%H:%M')
                await bot.send_message(chat_id=user_id,
                                       text=f'Завтра {date}г в {time} твоя подписка на Бота заканчивается! Чтобы  продолжать зарабатывать, продли подписку!\nPегистрация до {user_actual_status_}')
            if user_actual_status == twelve_hours_before.strftime('%Y-%m-%d %H:%M:%S'):
                user_actual_status_ = user['registered_to']
                
                date = user_actual_status_.strftime('%d %B %Y')
                english_month = user_actual_status_.strftime('%B')
                date = date.replace(english_month, months_translation[english_month])
                
                time = user_actual_status_.strftime('%H:%M')
                await bot.send_message(chat_id=user_id,
                                       text=f'Сегодня {date}г в {time} твоя подписка на Бота заканчивается! Чтобы  продолжать зарабатывать, продли подписку!\nPегистрация до {user_actual_status_}')
            if user_actual_status == one_day_after.strftime('%Y-%m-%d %H:%M:%S'):
                await bot.send_message(chat_id=user_id, text='Твоя подписка на Бота завершена. Пока бот закрывает старые сделки, ты еще можешь продлить подписку и вернуться к активной торговле без потерь. Через 7 дней все сделки из базы данных будут удалены')
            if user_actual_status == three_day_after.strftime('%Y-%m-%d %H:%M:%S'):
                await bot.send_message(chat_id=user_id, text='Твоя подписка на Бота завершена через 4 дня бот остановится. Все сделки и данные будут удалены. Не теряй свой шанс — вернись в строй!')
            if user_actual_status == seven_day_after.strftime('%Y-%m-%d %H:%M:%S'):
                await bot.send_message(chat_id=user_id, text='Остался последний день до полной остановки бота и удаления всех данных. Ты еще можешь продлить подписку и сохранить результаты. Не упусти прибыль!')
        await asyncio.sleep(1)
    