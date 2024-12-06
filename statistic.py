import datetime
from typing import List, Dict

from aiogram import Router, types, Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from config import PAIR_TABLE_MAP
from utils.calendar_ import SimpleCalAct, SimpleCalendarCallback, SimpleMonthCalendar, SimpleCalendar
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import get_all_open_sell_orders_autobuy_from_any_table

statistic_router = Router()

simple_calendar = SimpleCalendar()
mounth_calendar = SimpleMonthCalendar()



class TradeStatistics:
    def __init__(self, user_id: int, pair_table_map: Dict[str, str]):
        self.user_id = user_id
        self.pair_table_map = pair_table_map
        self.total_count = 0
        self.total_profit = 0.0

    async def _get_all_data_for_user(self):
        all_data = {}
        for pair, table in self.pair_table_map.items():
            all_data[pair] = await get_all_open_sell_orders_autobuy_from_any_table(self.user_id, pair, 2)
        return all_data

    def _calculate_statistics_for_period(self, trades: List[Dict], selected_date: str, filter_type: str) -> (int, float):
        count = 0
        profit = 0.0

        for trade in trades:
            try:
                if filter_type == "day":
                    transact_time_str = trade['transacttimesell'].strftime("%d.%m.%Y")
                elif filter_type == "month":
                    transact_time_str = trade['transacttimesell'].strftime("%m.%Y")
                else:
                    raise ValueError("Unknown filter type")

                if transact_time_str == selected_date:
                    count += 1
                    profit += trade['feelimitorder']
            except KeyError:
                continue

        return count, profit

    async def get_statistics_for_period(self, selected_date: str, filter_type: str) -> str:
        all_data = await self._get_all_data_for_user()
        statistics = []
        total_count = 0
        total_profit = 0.0

        for pair, trades in all_data.items():
            pair_count, pair_profit = self._calculate_statistics_for_period(trades, selected_date, filter_type)

            if pair_count > 0:
                statistics.append(
                    f"<b>{pair[:3]}/{pair[3:]}</b>\n"
                    f"Количество сделок: {pair_count}\n"
                    f"Прибыль: {round(pair_profit, 2)} {pair[3:]}\n"
                )
                total_count += pair_count
                total_profit += pair_profit
                
        summary = f"Прибыль за: {selected_date}\n\n" + "\n".join(statistics)
        summary += f"\n<b>Всего:\nКоличество сделок: {total_count}\nПрибыль: {round(total_profit, 2)} USDT</b>"
        
        return summary
    
    async def get_all_period(self, trades: List[Dict]):
        count = 0
        profit = 0.0
        
        for trade in trades:
            try:
                    count += 1
                    profit += trade['feelimitorder']
            except KeyError:
                continue
        
        return count, profit
    
    async def get_for_all_period_text(self):
        all_data = await self._get_all_data_for_user()
        statistics = []
        total_count = 0
        total_profit = 0.0
        
        for pair, trades in all_data.items():
            pair_count, pair_profit = await self.get_all_period(trades)
            
            if pair_count > 0:
                statistics.append(
                    f"<b>{pair[:3]}/{pair[3:]}</b>\n"
                    f"Количество сделок: {pair_count}\n"
                    f"Прибыль: {round(pair_profit, 2)} {pair[3:]}\n"
                )
                total_count += pair_count
                total_profit += pair_profit
        
        summary = "\n".join(statistics)
        summary += f"\n<b>Всего:</b>\nКоличество сделок: {total_count}\nПрибыль: {round(total_profit, 2)} USDT"
        return summary
    

async def handle_stats(message: types.Message, from_statistic=False, from_yesterday=None):
    user_id = message.from_user.id
    all_data = {}
    now = datetime.datetime.now().strftime("%d.%m.%Y")
    if from_yesterday:
        today = datetime.datetime.today().date()
        now = today - datetime.timedelta(days=1)
        now = now.strftime("%d.%m.%Y")
    
    for pair, table in PAIR_TABLE_MAP.items():
        all_data[pair] = await get_all_open_sell_orders_autobuy_from_any_table(user_id, pair, 2)
    
    trade_statistics = TradeStatistics(user_id, all_data)
    
    stats = await trade_statistics.get_statistics_for_period(now, "day")
    if from_statistic:
        return stats
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        InlineKeyboardButton(text="Дневная", callback_data="select_day"),
        InlineKeyboardButton(text="Месяц", callback_data="select_month"),
        InlineKeyboardButton(text="Полная", callback_data="select_full")
    )
    keyboard.adjust(1)
    
    await message.answer(stats, reply_markup=keyboard.as_markup())


@statistic_router.callback_query(SimpleCalendarCallback.filter())
async def handle_calendar_callback(callback: CallbackQuery, callback_data: SimpleCalendarCallback, bot: Bot):
    user_id = callback.from_user.id
    trade_statistics = TradeStatistics(user_id, PAIR_TABLE_MAP)
    
    if callback_data.act == SimpleCalAct.day:
        selected_date = f"{callback_data.day:02d}.{callback_data.month:02d}.{callback_data.year}"
        stats = await trade_statistics.get_statistics_for_period(selected_date, "day")
        await bot.edit_message_text(
            stats,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
    elif callback_data.act == SimpleCalAct.month:
        selected_month = f"{callback_data.month:02d}.{callback_data.year}"
        stats = await trade_statistics.get_statistics_for_period(selected_month, "month")
        await bot.edit_message_text(
            stats,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
    else:
        await simple_calendar.process_selection(callback, callback_data)


@statistic_router.callback_query(lambda call: call.data == "select_full")
async def process_full_selection(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    trade_statistics = TradeStatistics(user_id, PAIR_TABLE_MAP)
    res  = await trade_statistics.get_for_all_period_text()
    await bot.edit_message_text(
        res,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )


@statistic_router.callback_query(lambda call: call.data == "select_day")
async def handle_calendar_selection(callback: CallbackQuery, bot: Bot):
    if callback.data == "select_day":
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