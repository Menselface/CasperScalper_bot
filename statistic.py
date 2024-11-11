import datetime

from aiogram import Router, types, Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from utils.calendar_ import SimpleCalAct, SimpleCalendarCallback, SimpleMonthCalendar, SimpleCalendar
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import get_all_open_sell_orders_autobuy

statistic_router = Router()

simple_calendar = SimpleCalendar()
mounth_calendar = SimpleMonthCalendar()


async def handle_stats(message: types.Message):
    user_id = message.from_user.id
    all_data = await get_all_open_sell_orders_autobuy(user_id, 2)
    result = 0
    count = 0
    now = datetime.datetime.now().strftime("%d.%m.%Y")
    for data in all_data:
        transact_time_str = data['transacttimesell'].strftime("%d.%m.%Y")  # Преобразуем объект datetime в строку
        if transact_time_str == now:
            count += 1
            result += data['feelimitorder']
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="Дневная", callback_data="select_day"),
        InlineKeyboardButton(text="Месяц", callback_data="select_month"),
        InlineKeyboardButton(text="Полная", callback_data="select_full")
    )
    keyboard.adjust(1)
    
    await message.answer(f"<b>{now}</b>\n\nКоличество сделок: {count}\n Прибыль: {round(result, 2)} USDT",
                         reply_markup=keyboard.as_markup())


@statistic_router.callback_query(SimpleCalendarCallback.filter())
async def handle_calendar_callback(callback: CallbackQuery, callback_data: SimpleCalendarCallback, bot: Bot):
    user_id = callback.from_user.id
    all_data = await get_all_open_sell_orders_autobuy(user_id, 2)
    result = 0
    
    if callback_data.act == SimpleCalAct.day:
        count = 0
        selected_date = f"{callback_data.day:02d}.{callback_data.month:02d}.{callback_data.year}"
        
        for data in all_data:
            transact_time_str = data['transacttimesell'].strftime("%d.%m.%Y")
            if transact_time_str == selected_date:
                count += 1
                result += data['feelimitorder']
        
        await bot.edit_message_text(
            f'<b>{selected_date}</b>\n\nКоличество сделок: {count}\n Прибыль: {round(result, 2)} USDT',
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
    elif callback_data.act == SimpleCalAct.month:
        count = 0
        selected_month = f"{callback_data.month:02d}.{callback_data.year}"
        await callback.answer(f"Вы выбрали месяц: {selected_month}")
        for data in all_data:
            if data['transacttimesell'].strftime("%m.%Y") == selected_month:
                count += 1
                result += data['feelimitorder']
        await bot.edit_message_text(
            f'<b>{selected_month}</b>\n\nКоличество сделок: {count}\n Прибыль: {round(result, 2)} USDT',
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
    else:
        await simple_calendar.process_selection(callback, callback_data)


@statistic_router.callback_query(lambda call: call.data == "select_full")
async def process_full_selection(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    all_data = await get_all_open_sell_orders_autobuy(user_id, 2)
    result = 0
    count = 0
    await callback.answer("Вы выбрали полный отчет")
    for data in all_data:
        count += 1
        result += data['feelimitorder']
    
    await bot.edit_message_text(
        f'<b>За весь период</b>\n\nКоличество сделок: {count}\n Прибыль: {round(result, 2)} USDT',
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )


@statistic_router.callback_query(lambda call: call.data == "select_day")
async def handle_calendar_selection(callback: CallbackQuery, bot: Bot):
    if callback.data == "select_day":
        # Генерация календаря для выбора дня
        calendar_markup = await simple_calendar.start_calendar()
    
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=calendar_markup
    )


@statistic_router.callback_query(lambda call: call.data.startswith("select_month"))
async def process_month_selection(callback: CallbackQuery, bot: Bot):
    calendar_markup = await mounth_calendar.start_month_selector()
    await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=calendar_markup
    )
