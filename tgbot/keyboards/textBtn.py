from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardButton, InlineKeyboardBuilder
from aiogram import Bot, types


def choose_cat_button(categories):
    home_buttons = ReplyKeyboardBuilder()
    for i in categories:
        home_buttons.add(
            types.KeyboardButton(text=i)
        )
    home_buttons.adjust(1)
    return home_buttons
