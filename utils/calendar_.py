from enum import Enum
import calendar
from datetime import datetime, timedelta
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData
from pydantic import conlist, BaseModel, Field


class SimpleCalAct(str, Enum):
    ignore = 'IGNORE'
    prev_y = 'PREV-YEAR'
    prev_year = 'PREV-YEAR_'
    next_y = 'NEXT-YEAR'
    next_year = 'NEXT-YEAR_'
    prev_m = 'PREV-MONTH'
    next_m = 'NEXT-MONTH'
    cancel = 'CANCEL'
    today = 'TODAY'
    day = 'DAY'
    month = 'MONTH'


class CalendarCallback(CallbackData, prefix="calendar"):
    act: str
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None


class SimpleCalendarCallback(CalendarCallback, prefix="simple_calendar"):
    act: SimpleCalAct


class CalendarLabels(BaseModel):
    days_of_week: conlist(str, max_length=7, min_length=7) = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    months: conlist(str, max_length=12, min_length=12) = [
        "Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"
    ]
    cancel_caption: str = Field(default='Отмена', description='Надпись для кнопки отмены')
    today_caption: str = Field(default='Сегодня', description='Надпись для кнопки сегодня')


HIGHLIGHT_FORMAT = "[{}]"


def highlight(text):
    return HIGHLIGHT_FORMAT.format(text)


class SimpleCalendar:
    
    def __init__(self, labels: Optional[CalendarLabels] = None):
        self._labels = labels or CalendarLabels()
        self.ignore_callback = SimpleCalendarCallback(act=SimpleCalAct.ignore).pack()
    
    async def start_calendar(self, year: int = datetime.now().year,
                             month: int = datetime.now().month) -> InlineKeyboardMarkup:
        today = datetime.now()
        now_year, now_month, now_day = today.year, today.month, today.day
        
        def highlight_month():
            month_str = self._labels.months[month - 1]
            if now_month == month and now_year == year:
                return highlight(month_str)
            return month_str
        
        def highlight_day(day: int):
            day_string = str(day)
            if now_month == month and now_year == year and now_day == day:
                return highlight(day_string)
            return day_string
        
        kb = []
        
        # Год
        kb.append([
            InlineKeyboardButton(text="<<",
                                 callback_data=SimpleCalendarCallback(act=SimpleCalAct.prev_y, year=year, month=month,
                                                                      day=1).pack()),
            InlineKeyboardButton(text=str(year) if year != now_year else highlight(str(year)),
                                 callback_data=self.ignore_callback),
            InlineKeyboardButton(text=">>",
                                 callback_data=SimpleCalendarCallback(act=SimpleCalAct.next_y, year=year, month=month,
                                                                      day=1).pack())
        ])
        
        kb.append([
            InlineKeyboardButton(text="<",
                                 callback_data=SimpleCalendarCallback(act=SimpleCalAct.prev_m, year=year, month=month,
                                                                      day=1).pack()),
            InlineKeyboardButton(text=highlight_month(), callback_data=self.ignore_callback),
            InlineKeyboardButton(text=">",
                                 callback_data=SimpleCalendarCallback(act=SimpleCalAct.next_m, year=year, month=month,
                                                                      day=1).pack())
        ])
        
        kb.append([
            InlineKeyboardButton(text=weekday, callback_data=self.ignore_callback)
            for weekday in self._labels.days_of_week
        ])
        
        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            kb.append([
                InlineKeyboardButton(text=highlight_day(day) if day != 0 else " ",
                                     callback_data=SimpleCalendarCallback(act=SimpleCalAct.day, year=year, month=month,
                                                                          day=day).pack() if day != 0 else self.ignore_callback)
                for day in week
            ])
        
        kb.append([
            InlineKeyboardButton(text=self._labels.cancel_caption,
                                 callback_data=SimpleCalendarCallback(act=SimpleCalAct.cancel, year=year, month=month,
                                                                      day=1).pack()),
            InlineKeyboardButton(text=self._labels.today_caption,
                                 callback_data=SimpleCalendarCallback(act=SimpleCalAct.today, year=year, month=month,
                                                                      day=1).pack())
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=kb)
    
    async def process_selection(self, query: CallbackQuery, data: SimpleCalendarCallback) -> tuple:
        return_data = (False, None)
        
        if data.act == SimpleCalAct.ignore:
            await query.answer(cache_time=60)
            return return_data
        
        temp_date = datetime(int(data.year), int(data.month) if data.month else 1, 1)
        
        if data.act == SimpleCalAct.day:
            return_data = (True, datetime(int(data.year), int(data.month), int(data.day)))
            return return_data
        
        if data.act in {SimpleCalAct.prev_y, SimpleCalAct.next_y, SimpleCalAct.prev_m, SimpleCalAct.next_m}:
            if data.act == SimpleCalAct.prev_y:
                temp_date = temp_date.replace(year=temp_date.year - 1)
            elif data.act == SimpleCalAct.next_y:
                temp_date = temp_date.replace(year=temp_date.year + 1)
            elif data.act == SimpleCalAct.prev_m:
                temp_date = temp_date.replace(day=1) - timedelta(days=1)
            elif data.act == SimpleCalAct.next_m:
                temp_date = temp_date.replace(day=1) + timedelta(days=31)
            
            await self._update_calendar(query, temp_date)
        if data.act in {SimpleCalAct.next_year, SimpleCalAct.prev_year}:
            s = SimpleMonthCalendar()
            await s.process_selection(query, data)
        
        elif data.act == SimpleCalAct.today:
            today = datetime.now()
            if today.year != int(data.year) or today.month != int(data.month):
                await self._update_calendar(query, today)
            else:
                await query.answer(cache_time=60)
        elif data.act == SimpleCalAct.cancel:
            await query.message.delete_reply_markup()
        
        return return_data
    
    async def _update_calendar(self, query: CallbackQuery, with_date: datetime):
        await query.message.edit_reply_markup(
            reply_markup=await self.start_calendar(with_date.year, with_date.month)
        )


class SimpleMonthCalendar(SimpleCalendar):
    async def start_month_selector(self, year: int = datetime.now().year) -> InlineKeyboardMarkup:
        today = datetime.now()
        now_year, now_month = today.year, today.month
        
        def highlight_month(month: int):
            month_str = self._labels.months[month - 1]
            if now_year == year and now_month == month:
                return highlight(month_str)
            return month_str
        
        kb = []
        
        # Год
        kb.append([
            InlineKeyboardButton(text="<<",
                                 callback_data=SimpleCalendarCallback(act=SimpleCalAct.prev_year, year=year, month=1,
                                                                      day=1).pack()),
            InlineKeyboardButton(text=str(year) if year != now_year else highlight(str(year)),
                                 callback_data=self.ignore_callback),
            InlineKeyboardButton(text=">>",
                                 callback_data=SimpleCalendarCallback(act=SimpleCalAct.next_year, year=year, month=1,
                                                                      day=1).pack())
        ])
        
        for i in range(0, 12, 3):
            kb.append([
                InlineKeyboardButton(text=highlight_month(m),
                                     callback_data=SimpleCalendarCallback(act=SimpleCalAct.month, year=year, month=m,
                                                                          day=1).pack())
                for m in range(i + 1, i + 4)
            ])
        
        return InlineKeyboardMarkup(inline_keyboard=kb)
    
    async def process_selection(self, query: CallbackQuery, data: SimpleCalendarCallback) -> tuple:
        if data.act == SimpleCalAct.ignore:
            await query.answer(cache_time=60)
            return False, None
        
        year = data.year
        month = data.month
        
        if year is None or month is None:
            await query.answer("Некорректные данные.", cache_time=60)
            return False, None
        
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            await query.answer("Некорректные данные.", cache_time=60)
            return False, None
        
        if data.act == SimpleCalAct.month:
            selected_date = datetime(year, month, 1)
            return True, selected_date
        
        if data.act == SimpleCalAct.prev_year:
            prev_year = year - 1
            await self._update_calendar(query, with_date=datetime(prev_year, 1, 1), is_month_selector=True)
        
        if data.act == SimpleCalAct.next_year:
            next_year = year + 1
            await self._update_calendar(query, with_date=datetime(next_year, 1, 1), is_month_selector=True)
        
        return False, None
    
    async def _update_calendar(self, query: CallbackQuery, with_date: datetime, is_month_selector: bool = False):
        if is_month_selector:
            await query.message.edit_reply_markup(reply_markup=await self.start_month_selector(with_date.year))
        else:
            await super()._update_calendar(query, with_date)
