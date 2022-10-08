from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup


class reg_user(StatesGroup):
    name = State()
    phone = State()
    
class make_req(StatesGroup):
    name = State()
    cat = State()
    delivers = State()
    city = State()
    comment = State()
