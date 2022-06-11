from aiogram.dispatcher.filters.state import StatesGroup, State


class CalcMenuStates(StatesGroup):
    s_names = State()
    got_s_names = State()
    s_coords = State()
    got_s_coords = State()


class ClimateZoneMenuStates(StatesGroup):
    climate_zone_state = State()


class BotInfMenuStates(StatesGroup):
    bot_inf_state = State()
