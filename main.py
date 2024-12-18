from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from admin import handle_admin, admin_router
from balance.balance import handle_balance
from config import TOKEN
from fee import fee_router, get_user_commission_keybs
from first_reg import handle_start, handle_registration, registration_states_router
from parameters import parameters_router, handle_parameters_choice_symbol
from price import handle_price
from statistic import handle_stats, statistic_router
from status import status_router, handle_status_command
from subs import handle_subs
from orders_checker import start_orders_checker
from trading.start_trade import user_start_trade
from utils.additional_methods import create_logs
from utils.registration_ending import final_of_registration_date
from utils.send_and_pin_message import send_and_pin
from utils.trading_view_analyze import handle_start_trading_view
from utils.user_setup_symbols import user_set_up
from utils.user_setup_symbols import user_setup_router


bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_routers(
    registration_states_router,
            status_router,
            parameters_router,
            statistic_router,
            admin_router,
            user_setup_router,
            user_start_trade,
            fee_router
                    )


@dp.message(Command('start'))
async def start_command(message: types.Message):
    await handle_start(message, bot)


@dp.message(StateFilter(None), Command('registration'))
async def registration_command(message: types.Message, state: FSMContext):
    await handle_registration(message, state)


@dp.message(Command('parameters'))
async def parameters_command(message: types.Message, state: FSMContext):
    await handle_parameters_choice_symbol(message, state, bot)


@dp.message(Command('statistics'))
async def stats_command(message: types.Message):
    await handle_stats(message)


@dp.message(Command('balance'))
async def balance_command(message: types.Message, bot: Bot):
    await handle_balance(message, bot)


@dp.message(Command('orders'))
async def status_command(message: types.Message):
    await handle_status_command(message)


@dp.message(Command('price'))
async def price_command(message: types.Message):
    await handle_price(message)
    

@dp.message(Command('trade'))
async def go_work_command(message: types.Message, bot: Bot, state: FSMContext):
    await user_set_up(message, bot, state)
    
    
@dp.message(F.text.lower() == "админ")
async def admin_panel(message: types.Message, bot: Bot, state: FSMContext):
    await handle_admin(message, bot, state)
    
@dp.message(Command('fee'))
async def stop_command(message: types.Message, state: FSMContext, bot: Bot):
    await get_user_commission_keybs(message, state, bot)


@dp.message(Command('subs'))
async def subs_command(message: types.Message):
    await handle_subs(message, bot)


async def main():
    schedule = AsyncIOScheduler(timezone='Europe/Kiev')
    bot_info = await bot.get_me()
    logger.info(f"Бот @{bot_info.username} id={bot_info.id} - '{bot_info.first_name}' запустился")
    try:
        schedule.add_job(
            send_and_pin,
            trigger='cron',
            hour=0,
            minute=0,
            start_date=datetime.now(),
            kwargs={'bot': bot}
        )
        logger.info("Закреп в 12.00 запущен")
        
        schedule.add_job(final_of_registration_date, kwargs={'bot': bot})
        logger.info("Проверка конца регистраций для пользователей запущенна")
        
        schedule.add_job(start_orders_checker, kwargs={'bot': bot})
        schedule.add_job(handle_start_trading_view, kwargs={'bot': bot})
        
        schedule.start()
        await bot.delete_webhook(drop_pending_updates=True)
        await create_logs()
        await dp.start_polling(bot)
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        if schedule.running:
            schedule.shutdown(wait=False)
            logger.info("Scheduler stopped.")


if __name__ == '__main__':
    import asyncio
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")