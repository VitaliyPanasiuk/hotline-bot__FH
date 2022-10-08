from aiogram import Router, Bot, types
from aiogram.types import Message, FSInputFile
from tgbot.config import load_config
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs

from tgbot.misc.states import reg_user,make_req
from tgbot.misc.functions import auf

from tgbot.keyboards.textBtn import choose_cat_button
from tgbot.keyboards.inlineBtn import choose_delivery_button


import requests
from bs4 import BeautifulSoup
import re


buyer_router = Router()
config = load_config(".env")
bot2 = Bot(token=config.tg_bot.token2, parse_mode='HTML')
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')

base = psycopg2.connect(dbname=config.db.database, user=config.db.user, password=config.db.password,host=config.db.host)
cur = base.cursor()