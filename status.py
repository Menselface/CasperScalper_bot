from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime
from typing import List
from contextlib import suppress
from trading import is_working

from db import get_all_open_sell_orders_autobuy, get_user_stop_buy_status
from first_reg import check_status_of_registration

status_router = Router()


class TextStartsWithFilter(BaseFilter):
    def __init__(self, startswith: str):
        self.startswith = startswith
    
    async def __call__(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data.startswith(self.startswith)


async def handle_status(message: Message):
    user_id = message.from_user.id
    
    all_data_from_db = await get_all_open_sell_orders_autobuy(user_id, 1)
    all_data_from_db_with_nine = await get_all_open_sell_orders_autobuy(user_id, 9)
    
    # Сортировка записей по времени (по убыванию)
    sorted_records = sorted(all_data_from_db, key=lambda x: x['transacttimebuy'], reverse=True)
    sorted_records.extend(all_data_from_db_with_nine)
    total_orders_len = str(len(sorted_records))
    
    # Разбиение на группы по 5 записей
    grouped_records = [sorted_records[i:i + 5] for i in range(0, len(sorted_records), 5)]
    total_pages = len(grouped_records)
    
    # Отправка первой страницы записей
    message_id = await send_paginated_message(message, grouped_records, 1, total_pages, total_orders_len)


async def send_paginated_message(message: Message, grouped_records: List[List[dict]], current_page: int,
                                 total_pages: int, total_orders_len: str):
    records = grouped_records[current_page - 1]
    user_id = message.from_user.id
    all_data_from_db = await get_all_open_sell_orders_autobuy(user_id, 1)
    if len(all_data_from_db) < 1:
        is_working.is_working = False
        is_working.remove_user(user_id)
    if len(records) < 1:
        await message.answer("У вас нет активных ордеров")
        return
    messages = []
    number = 1 + (current_page - 1) * 5
    checker_autobuy = is_working.user_real_autobuy_checker(user_id)
    stop_stats = await get_user_stop_buy_status(user_id)
    
    
    for index, record in enumerate(records):
        # Определение префикса для самой последней записи
        prefix = " <b>(GENERAL)</b>" if index == 0 and checker_autobuy and stop_stats == 0 else ""
        
        
        qtytosell = record.get('qtytosell', None)
        priceorderbuy = record.get('priceorderbuy', None)
        totalamountonpurchace = record.get('totalamountonpurchace', None)
        priceordersell = record.get('priceordersell', None)
        
        qtytosell = f"{float(qtytosell):.5g}" if qtytosell is not None else '0'
        priceorderbuy = f"{float(priceorderbuy):.6g}" if priceorderbuy is not None else '0'
        totalamountonpurchace = f"{float(totalamountonpurchace):.5g}" if totalamountonpurchace is not None else '0'
        priceordersell = f"{float(priceordersell):.6g}" if priceordersell is not None else '0'
        
        totalamountaftersale = record.get('totalamountaftersale', None)
        totalsellamount = f"{float(qtytosell) * float(priceordersell):.5g}" if qtytosell and priceordersell else '0'
        
        months = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        
        message_date = record['transacttimebuy']
        day = message_date.day
        month = months[message_date.month]
        year = message_date.year
        time = message_date.strftime("%H:%M:%S")
        
        formatted_date = f"{day} {month} {year} {time}"
        message_user = (f"{number}. Ордер на продажу{prefix}\n"
                        f"{qtytosell} KAS\n"
                        f"- Куплено по {priceorderbuy} ({totalamountonpurchace}) USDT\n"
                        f"- Продается по {priceordersell} ({totalsellamount}) USDT\n"
                        f"{formatted_date}")
        messages.append(message_user)
        number += 1
    
    await message.answer(f"<b>Всего ордеров - {total_orders_len}\n\n</b>" + "\n\n".join(messages), reply_markup=create_pagination_keyboard(current_page, total_pages))


def create_pagination_keyboard(current_page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    
    if current_page > 1:
        builder.button(text="<<", callback_data="page:1")
        builder.button(text="<", callback_data=f"page:{current_page - 1}")
    else:
        builder.button(text="<<", callback_data="page:1", disabled=True)
        builder.button(text="<", callback_data=f"page:{current_page - 1}", disabled=True)
    
    builder.button(text=f"{current_page} ({total_pages})", callback_data="current_page")
    
    if current_page < total_pages:
        builder.button(text=">", callback_data=f"page:{current_page + 1}")
        builder.button(text=">>", callback_data=f"page:{total_pages}")
    else:
        builder.button(text=">", callback_data=f"page:{current_page + 1}", disabled=True)
        builder.button(text=">>", callback_data=f"page:{total_pages}", disabled=True)
    
    return builder.as_markup()


@status_router.callback_query(TextStartsWithFilter(startswith="page:"))
async def handle_pagination(query: CallbackQuery):
    page_number = int(query.data.split(":")[1])
    
    if page_number <= 0:
        return
    user_id = query.from_user.id
    stop_stats = await get_user_stop_buy_status(user_id)
    checker_autobuy = is_working.user_real_autobuy_checker(user_id)
    with suppress(TelegramBadRequest, IndexError):
        all_data_from_db = await get_all_open_sell_orders_autobuy(user_id, 1)
        all_data_from_db_with_nine = await get_all_open_sell_orders_autobuy(user_id, 9)
        
        # Сортировка записей по времени (по убыванию)
        sorted_records = sorted(all_data_from_db, key=lambda x: x['transacttimebuy'], reverse=True)
        sorted_records.extend(all_data_from_db_with_nine)
        grouped_records = [sorted_records[i:i + 5] for i in range(0, len(sorted_records), 5)]
        total_pages = len(grouped_records)
        total_orders_len = str(len(sorted_records))
        
        # Получить записи для текущей страницы
        records = grouped_records[page_number - 1]
        messages = []
        number = 1 + (page_number - 1) * 5
        for index, record in enumerate(records):
            prefix = " <b>(GENERAL)</b>" if index == 0 and checker_autobuy and page_number == 1 and stop_stats == 0 else ""
            qtytosell = record.get('qtytosell', None)
            priceorderbuy = record.get('priceorderbuy', None)
            totalamountonpurchace = record.get('totalamountonpurchace', None)
            priceordersell = record.get('priceordersell', None)
            
            qtytosell = f"{float(qtytosell):.5g}" if qtytosell is not None else '0'
            priceorderbuy = f"{float(priceorderbuy):.6g}" if priceorderbuy is not None else '0'
            totalamountonpurchace = f"{float(totalamountonpurchace):.5g}" if totalamountonpurchace is not None else '0'
            priceordersell = f"{float(priceordersell):.6g}" if priceordersell is not None else '0'
            
            totalamountaftersale = record.get('totalamountaftersale', None)
            totalsellamount = f"{float(qtytosell) * float(priceordersell):.5g}" if qtytosell and priceordersell else '0'
            
            months = {
                1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
                5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
                9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
            }
            
            message_date = record['transacttimebuy']  # используем время из записи
            day = message_date.day
            month = months[message_date.month]
            year = message_date.year
            time = message_date.strftime("%H:%M:%S")
            
            formatted_date = f"{day} {month} {year} {time}"
            message_user = (f"{number}. Ордер на продажу {prefix}\n"
                            f"{qtytosell} KAS\n"
                            f"- Куплено по {priceorderbuy} ({totalamountonpurchace}) USDT\n"
                            f"- Продается по {priceordersell} ({totalsellamount}) USDT\n"
                            f"{formatted_date}")
            messages.append(message_user)
            number += 1
        if page_number == 1:
            await query.message.edit_text(f"<b>Всего ордеров - {total_orders_len}\n\n</b>" +"\n\n".join(messages),
                                      reply_markup=create_pagination_keyboard(page_number, total_pages))
        else:
            await query.message.edit_text("\n\n".join(messages),
                                          reply_markup=create_pagination_keyboard(page_number, total_pages))
        await query.answer()
