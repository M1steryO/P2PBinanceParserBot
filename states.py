from aiogram.fsm.state import StatesGroup, State


class Settings(StatesGroup):
    choosing_max_limit = State()
    choosing_rate = State()
