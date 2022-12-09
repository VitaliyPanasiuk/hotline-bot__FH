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
    # example.row(types.InlineKeyboardButton(
    #     text=f'Закрити замовлення',
    #     callback_data='end'
    # ))
    return example

def end_button(order):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Закрити замовлення", callback_data=SellersCallbackFactory(action="end_order", order_id=int(order))
    )
    return builder

def choose_delivery_button(arr):
    example = InlineKeyboardBuilder()
    example.row(types.InlineKeyboardButton(
        text=f'Нова Пошта {"🟢" if "nova_pochta" in arr else "🔴"}',
        callback_data='nova_pochta'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'САТ {"🟢" if "nalp" in arr else "🔴"}',
        callback_data='nalp'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Укрпошта {"🟢" if "ukr_pochta" in arr else "🔴"}',
        callback_data='ukr_pochta'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Делівері {"🟢" if "del" in arr else "🔴"}',
        callback_data='del'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Міст {"🟢" if "mist" in arr else "🔴"}',
        callback_data='mist'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Самовивіз {"🟢" if "samo" in arr else "🔴"}',
        callback_data='samo'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Готово ✅',
        callback_data='deliveri_done'
    ))
    return example

def choose_payment_button(arr):
    example = InlineKeyboardBuilder()
    example.row(types.InlineKeyboardButton(
        text=f'Накладений платіж {"🟢" if "nak" in arr else "🔴"}',
        callback_data='nak'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Передплата на картку {"🟢" if "pred" in arr else "🔴"}',
        callback_data='pred'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Безготівкова без ПДВ  {"🟢" if "card" in arr else "🔴"}',
        callback_data='card'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Безготівкова з ПДВ  {"🟢" if "card_pdv" in arr else "🔴"}',
        callback_data='card_pdv'
    ))
    example.row(types.InlineKeyboardButton(
        text=f'Готово ✅',
        callback_data='payment_done'
    ))
    return example

def accept_order_btn(order):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Прийняти", callback_data=SellersCallbackFactory(action="accept_order", order_id=int(order))
    )
    builder.button(
        text="Відхилити", callback_data=SellersCallbackFactory(action="delete_order", order_id=int(order))
    )
    return builder

# order_price,order_term,order_com,
def accept_order_buyer_btn(seller_id,order_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Прийняти", callback_data=SellersCallbackFactory(action="accept_order_buyer", seller_id=str(seller_id),order_id=int(order_id))
    )
    return builder
