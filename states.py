from aiogram.fsm.state import StatesGroup, State


class AddWish(StatesGroup):
    writing_wish_name = State()
    writing_wish_price = State()
    writing_wish_description = State()
    sending_wish_photo = State()
    sending_wish_url = State()
    database = State()


class DelWish(StatesGroup):
    deleting_wish = State()


class CheckWish(StatesGroup):
    choosing_item_wl = State()


class AddFriend(StatesGroup):
    sending_contact = State()
    checking_requests = State()
    deleting_request = State()
    deleting_friend = State()
    accepting_request = State()
    choosing_item = State()
    viewing_wishlist = State()
    viewing_item_wl = State()
