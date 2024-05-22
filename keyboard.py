from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

menu_buttons = [
    KeyboardButton(text="Вишлист"),
    KeyboardButton(text="Друзья"),
    KeyboardButton(text="Меню")
]
wishlist_buttons = [
    KeyboardButton(text="Добавить в Вишлист"),
    KeyboardButton(text="Удалить из Вишлиста"),
    KeyboardButton(text="Посмотреть Вишлист"),
    KeyboardButton(text="Меню")
]
friends_buttons = [
    KeyboardButton(text="Добавить в Друзья"),
    KeyboardButton(text="Посмотреть вишлист Друга"),
    KeyboardButton(text="Посмотреть входящие заявки"),
    KeyboardButton(text="Удалить из Друзей"),
    KeyboardButton(text="Посмотреть Друзей"),
    KeyboardButton(text="Меню")
]
wish_builder = ReplyKeyboardBuilder()
friends_builder = ReplyKeyboardBuilder()
menu_builder = ReplyKeyboardBuilder()

for btn in wishlist_buttons:
    wish_builder.add(btn)
wish_builder.adjust(1)

wishlist_kb = wish_builder.as_markup(
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)

for btn in menu_buttons:
    menu_builder.add(btn)
menu_builder.adjust(1)

menu_kb = menu_builder.as_markup(
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)

for btn in friends_buttons:
    friends_builder.add(btn)
friends_builder.adjust(1)

friend_kb = friends_builder.as_markup(
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)


def make_row_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)


def make_num_keyboard(items: list[str]):
    builder = ReplyKeyboardBuilder()
    for i, _ in enumerate(items):
        builder.add(KeyboardButton(text=str(i + 1)))

    builder.add(KeyboardButton(text='Отменить'))
    builder.adjust(4)
    return builder.as_markup(resize_keyboard=True)
