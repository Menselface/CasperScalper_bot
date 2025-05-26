from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import *
from bot.handlers.start import start_router
from config import TOKEN
from orders_checker import start_orders_checker
from services.sessions.session_revival import start_session_revival
from test_sample import on_startup
from utils.additional_methods import identify_myself
from utils.inactive_users import remove_inactive_users
from utils.logger import logger
from utils.middlewares import RateLimitMiddleware, CheckUserActiveMiddleware
from utils.registration_ending import final_of_registration_date
from utils.send_and_pin_message import send_and_pin, send_and_pin_month

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.message.middleware(RateLimitMiddleware())
dp.message.middleware(CheckUserActiveMiddleware())
dp.startup.register(on_startup)

dp.include_routers(
    admin_router,
            help_router,
            order_status_router,
            parameters_router,
            price_router,
            start_router,
            statistic_router,
            subscription_info_router,
                    )


async def main():
    schedule = AsyncIOScheduler(timezone='Europe/Kiev')
    bot_info = await bot.get_me()
    logger.log("BOOT", f"Бот @{bot_info.username} id={bot_info.id} {await identify_myself()}")
    try:
        schedule.add_job(
            send_and_pin,
            trigger='cron',
            hour=0,
            minute=0,
            start_date=datetime.now(),
            kwargs={'bot': bot}
        )
        logger.log("BOOT","Закреп в 12.00 запущен")

        schedule.add_job(
            send_and_pin_month,
            trigger='cron',
            hour=23,
            minute=59,
            start_date=datetime.now(),
            kwargs={'bot': bot}
        )
        logger.log("BOOT","Закреп в 11.59 запущен")

        schedule.add_job(
            final_of_registration_date,
            trigger='cron',
            hour=9,
            minute=0,
            kwargs={'bot': bot}
        )
        logger.log("BOOT","Проверка конца регистраций для пользователей запущенна")
        
        schedule.add_job(start_orders_checker, trigger='interval', minutes=5, kwargs={'bot': bot})
        schedule.add_job(start_session_revival, trigger='interval', minutes=15, kwargs={'bot': bot})
        schedule.add_job(remove_inactive_users, trigger='cron', hour=9, minute=0)
        schedule.start()
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    
    except KeyboardInterrupt:
        logger.log("BOOT","Bot stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        if schedule.running:
            schedule.shutdown(wait=False)
            logger.log("BOOT","Scheduler stopped.")


if __name__ == '__main__':
    import asyncio
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.log("BOOT","Bot stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
