from aiogram import Bot
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import get_all_open_sell_orders_autobuy_from_any_table
from keyboards import PairCallback, create_pair_selection_keyboard, create_pagination_keyboard
from parameters import delete_message
from utils.additional_methods import safe_format, format_symbol, user_active_pair

status_router = Router()


async def handle_status_command(message: Message):
    await message.answer("Выберите валютную пару:", reply_markup=create_pair_selection_keyboard())


@status_router.callback_query(PairCallback.filter())
async def handle_pair_selection(callback: CallbackQuery, callback_data: PairCallback, state: FSMContext, bot: Bot):
    pair = callback_data.pair
    user_id = callback.from_user.id
    await callback.answer(f"Вы выбрали пару {pair}. Загружаю ордера...", cache_time=4)
    
    all_data_from_db = await get_all_open_sell_orders_autobuy_from_any_table(user_id, pair, 1)
    all_data_from_db_with_nine = await get_all_open_sell_orders_autobuy_from_any_table(callback.from_user.id, pair, 9)
    
    sorted_records = sorted(all_data_from_db, key=lambda x: x['transacttimebuy'], reverse=True)
    sorted_records.extend(all_data_from_db_with_nine)
    grouped_records = [sorted_records[i:i + 5] for i in range(0, len(sorted_records), 5)]
    
    if not sorted_records:
        await callback.message.edit_text(f"У вас нет активных ордеров для пары {pair}.")
        return
    
    await send_paginated_message(callback.message, grouped_records, 1, len(grouped_records), len(sorted_records), pair, state, bot)


async def send_paginated_message(message: Message, grouped_records: list, current_page: int,
                                 total_pages: int, total_orders_len: int, pair: str, state: FSMContext, bot: Bot):
    records = grouped_records[current_page - 1]
    number = 1 + (current_page - 1) * 5
    messages = []
    data = await state.get_data()
    status_message_id = data.get("status_message_id")
    user_id = message.chat.id
    is_user_trade_now = await user_active_pair(user_id, pair)
    
    for record in records:
        qtytosell = record.get('qtytosell', '0')
        priceorderbuy = record.get('priceorderbuy', '0')
        totalamountonpurchace = record.get('totalamountonpurchace', '0')
        priceordersell = record.get('priceordersell', '0')
        totalsellamount = f"{float(qtytosell) * float(priceordersell):.3g}" if qtytosell and priceordersell else '0'
        
        message_date = record['transacttimebuy']
        formatted_date = message_date.strftime("%d.%m.%Y %H:%M:%S")
        
        if pair == "KASUSDT":
            messages.append(
                f"{number}. Ордер на продажу\n"
                f"{safe_format(qtytosell, 2)} {format_symbol(pair)}\n"
                f"- Куплено по {safe_format(priceorderbuy, 6)} ({safe_format(totalamountonpurchace, 2)} USDT)\n"
                f"- Продается по {safe_format(priceordersell, 6)} ({safe_format(totalsellamount, 2)} USDT)\n"
                f"{formatted_date}"
            )
        else:
            messages.append(
                f"{number}. Ордер на продажу\n"
                f"{safe_format(qtytosell, 6)} {format_symbol(pair)}\n"
                f"- Куплено по {safe_format(priceorderbuy, 2)} ({safe_format(totalamountonpurchace, 2)} USDC)\n"
                f"- Продается по {safe_format(priceordersell, 2)} ({safe_format(totalsellamount, 2)} USDC)\n"
                f"{formatted_date}"
            )
            
        number += 1
    header = f"{format_symbol(pair)}    {' ✅ торгует' if is_user_trade_now else '⬛️ OFF'}" if current_page == 1 else ""
    result_text = f"{header}\n\n<b>Всего ордеров - {total_orders_len}</b>\n\n" + "\n\n".join(messages)
    await delete_message(user_id, status_message_id, bot)
    mes = await bot.send_message(
        chat_id=user_id,
        text=result_text,
        reply_markup=create_pagination_keyboard(current_page, total_pages, pair)
    )
    await state.update_data(status_message_id=mes.message_id)


@status_router.callback_query(lambda callback: callback.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery, state: FSMContext, bot: Bot):
    _, page, pair = callback.data.split(":")
    page = int(page)
    
    all_data_from_db = await get_all_open_sell_orders_autobuy_from_any_table(callback.from_user.id, pair, 1)
    all_data_from_db_with_nine = await get_all_open_sell_orders_autobuy_from_any_table(callback.from_user.id, pair, 9)
    
    sorted_records = sorted(all_data_from_db, key=lambda x: x['transacttimebuy'], reverse=True)
    sorted_records.extend(all_data_from_db_with_nine)
    grouped_records = [sorted_records[i:i + 5] for i in range(0, len(sorted_records), 5)]
    
    if not grouped_records:
        await callback.message.edit_text(f"У вас нет активных ордеров для пары {pair}.")
        return
    
    await send_paginated_message(callback.message, grouped_records, page, len(grouped_records), len(sorted_records),
                                 pair, state, bot)
