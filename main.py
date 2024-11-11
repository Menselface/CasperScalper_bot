# main.py

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timezone, datetime

from loguru import logger

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from admin import handle_admin, admin_router
from config import TOKEN
from first_reg import handle_start, handle_registration, registration_states_router
from parameters import handle_parameters, parameters_router
from buy_market import handle_buy
from statistic import handle_stats, statistic_router
from balance import handle_balance
from status import handle_status, status_router
from price import handle_price
from trading import handle_autobuy, orders_checker, orders_checker_onlly_nine
from stop import handle_stop
from subs import handle_subs
from utils.registration_ending import final_of_registration_date
from utils.send_and_pin_message import send_and_pin

# Инициализация логгирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_router(registration_states_router)
dp.include_router(status_router)
dp.include_router(parameters_router)
dp.include_router(statistic_router)
dp.include_router(admin_router)


# Обработчики команд
@dp.message(Command('start'))
async def start_command(message: types.Message):
    await handle_start(message, bot)


@dp.message(StateFilter(None), Command('registration'))
async def registration_command(message: types.Message, state: FSMContext):
    await handle_registration(message, state)


@dp.message(Command('parameters'))
async def parameters_command(message: types.Message, state: FSMContext):
    await handle_parameters(message, state, bot)


@dp.message(Command('buy'))
async def buy_command(message: types.Message):
    await handle_buy(message, bot)


@dp.message(Command('stats'))
async def stats_command(message: types.Message):
    await handle_stats(message)


@dp.message(Command('balance'))
async def balance_command(message: types.Message, bot: Bot):
    await handle_balance(message, bot)


@dp.message(Command('status'))
async def status_command(message: types.Message):
    await handle_status(message)


@dp.message(Command('price'))
async def price_command(message: types.Message):
    await handle_price(message)

@dp.message(Command('run_forrest_run'))
async def go_work_command(message: types.Message, bot: Bot):
    await handle_autobuy(message, bot)
    # await orders_checker(message, bot, current_order_id='C02__475019225245814784037')
    
    
@dp.message(F.text.lower() == "админ")
async def admin_panel(message: types.Message, bot: Bot, state: FSMContext):
    await handle_admin(message, bot, state)
    
# поменять команду stop на stop_buy
@dp.message(Command('stop'))
async def stop_command(message: types.Message, bot: Bot):
    await handle_stop(message, bot)


@dp.message(Command('subs'))
async def subs_command(message: types.Message):
    await handle_subs(message, bot)


@dp.message(Command('help'))
async def help_command(message: types.Message):
    help_text = (
        "v. 1.102\n"
        "Добро пожаловать в торгового бота для KASPA на бирже MEXC!\n\n"
        "Команды:\n"
        "/start - Начало работы\n"
        "/registration - Регистрация\n"
        "/parameters - Настройка параметров\n"
        "/buy - Покупка по рынку\n"
        "/stats - Статистика прибыли\n"
        "/balance - Проверка баланса\n"
        "/status - Статус бота\n"
        "/price - Текущая цена KASPA\n"
        "/run_forrest_run - Запуск автопокупки\n"
        "/stop - Остановка автопокупки\n"
        "/subs - Проверка подписки\n"
        "/help - Помощь и справочная информация\n"
    )

    await message.reply(help_text, parse_mode='HTML', disable_web_page_preview=True)


# Запуск бота
async def main():
    schedule = AsyncIOScheduler(timezone='Europe/Kiev')
    schedule.add_job(send_and_pin, trigger='cron', hour=0, minute=0, start_date=datetime.now(),  kwargs={'bot': bot})
    schedule.add_job(final_of_registration_date, kwargs={'bot': bot})
    schedule.start()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    import asyncio
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")