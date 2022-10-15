from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardButton, InlineKeyboardBuilder
from aiogram import Bot, types
from typing import Optional
from aiogram.dispatcher.filters.callback_data import CallbackData

class SellersCallbackFactory(CallbackData, prefix="fabnum"):
    action: str
    order_id: Optional[int]
    seller_id: Optional[str]
    price: Optional[str]
    term: Optional[str]
    com: Optional[str]


def homeB_button():
    example = InlineKeyboardBuilder()
    example.row(types.InlineKeyboardButton(
        text=f'Почати пошук',
        callback_data='buy'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Закрити замовлення',
        callback_data='end'
    ))
    return example
def homeS_button():
    example = InlineKeyboardBuilder()
    example.row(types.InlineKeyboardButton(
        text=f'Закрити замовлення',
        callback_data='endsellar'
    ))
    return example

def choose_delivery_button(arr):
    example = InlineKeyboardBuilder()
    example.row(types.InlineKeyboardButton(
        text=f'Новая почта {"🟢" if "nova_pochta" in arr else "🔴"}',
        callback_data='nova_pochta'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Наложеный платеж {"🟢" if "nalp" in arr else "🔴"}',
        callback_data='nalp'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Укр почта {"🟢" if "ukr_pochta" in arr else "🔴"}',
        callback_data='ukr_pochta'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Готово ✅',
        callback_data='deliveri_done'
    ))
    return example

def accept_order_btn(order):
    builder = InlineKeyboardBuilder()
    print(order)
    print(type(order))
    builder.button(
        text="Прийняти", callback_data=SellersCallbackFactory(action="accept_order", order_id=int(order))
    )
    return builder

def accept_order_buyer_btn(seller_id,order_price,order_term,order_com,order_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Прийняти", callback_data=SellersCallbackFactory(action="accept_order_buyer", seller_id=str(seller_id),price = str(order_price),term = str(order_term),com = str(order_com),order_id=int(order_id))
    )
    return builder
