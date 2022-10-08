from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardButton, InlineKeyboardBuilder
from aiogram import Bot, types


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
