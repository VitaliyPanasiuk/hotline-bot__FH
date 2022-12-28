import email
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup


class reg_user(StatesGroup):
    name = State()
    phone = State()
    org = State()
    email = State()

class end_order(StatesGroup):
    id = State()
    rate = State()
    action = State()

class accept_ord(StatesGroup):
    id = State()
    price = State()
    comment = State()
    terms = State()
    seller_id = State()
    
class make_req(StatesGroup):
    name = State()
    cat = State()
    min_max = State()
    delivers = State()
    payment = State()
    city = State()
    comment = State()
    mes_id = State()
