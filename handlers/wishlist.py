from aiogram import Router, types, F, html
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import dotenv_values

from states import AddWish, DelWish, CheckWish
from keyboard import wishlist_kb, menu_kb, make_row_keyboard, make_num_keyboard
from database.models import User, Wishlist
from texts import texts


config = dotenv_values('.env')
database_url = config['DATABASE_URL']

engine = create_engine(database_url, echo=True, pool_recycle=7200)
session = Session(engine)

router = Router()


@router.message(Command('start'))
async def start_handler(message: Message):

    user_fullname = html.quote(message.from_user.full_name)
    user_id = message.from_user.id
    user = session.query(User).filter_by(
        user_id=user_id).first()

    if user is None:
        user = User(name=user_fullname, user_id=user_id)
        session.add(user)
        session.commit()

    await message.answer(
        texts['greet'].format(username=user_fullname),
        reply_markup=menu_kb
    )


@router.message(F.text.lower() == "вишлист")
async def wishlist_reply(message: Message):
    await message.answer(
        texts['wl'],
        reply_markup=wishlist_kb
    )


@router.message(StateFilter(None), F.text.lower().in_(
    {
        "добавить в вишлист", "создать вишлист"
    }
))
async def add_to_wishlist_reply(message: Message, state: FSMContext):
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    if user is None:
        await message.answer(
            "Введите команду /start для запуска бота"
        )
        await state.clear()
        return

    else:
        await message.answer(
            texts["add_name_wl"],
            reply_markup=make_row_keyboard(["Отменить"])
        )
        await state.set_state(AddWish.writing_wish_name)


@router.message(AddWish.writing_wish_name)
async def wish_name_written(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        texts["add_price"],
        reply_markup=make_row_keyboard(["Не указывать", "Отменить"])
    )
    await state.set_state(AddWish.writing_wish_price)


@router.message(
    AddWish.writing_wish_price,
    F.text.lower() == "не указывать"
)
async def wish_price_not_written(message: Message, state: FSMContext):
    await state.update_data(price=None)
    await message.answer(
        texts["add_description"],
        reply_markup=make_row_keyboard(["Не добавлять", "Отменить"])
    )
    await state.set_state(AddWish.writing_wish_description)


@router.message(AddWish.writing_wish_price)
async def wish_price_written(message: Message, state: FSMContext):
    try:
        price = int(message.text)

    except ValueError:
        await message.answer(texts['price_error'])
        await state.set_state(AddWish.writing_wish_price)

    await state.update_data(price=int(message.text))
    await message.answer(
        texts["add_description"],
        reply_markup=make_row_keyboard(["Не добавлять", "Отменить"])
    )
    await state.set_state(AddWish.writing_wish_description)


@router.message(
    AddWish.writing_wish_description,
    F.text.lower() == "не добавлять"
)
async def wish_description_not_written(message: Message, state: FSMContext):
    await state.update_data(description=None)
    await message.answer(
        texts["add_photo"],
        reply_markup=make_row_keyboard(["Без фото", "Отменить"])
    )
    await state.set_state(AddWish.sending_wish_photo)


@router.message(AddWish.writing_wish_description)
async def wish_description_written(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        texts["add_photo"],
        reply_markup=make_row_keyboard(["Без фото", "Отменить"])
    )
    await state.set_state(AddWish.sending_wish_photo)


@router.message(
    AddWish.sending_wish_photo,
    F.text.lower() == "без фото"
)
async def wish_photo_not_sent(message: Message, state: FSMContext):
    await state.update_data(photo_id=None)
    await message.answer(
        texts["add_link"],
        reply_markup=make_row_keyboard(["Не присылать", "Отменить"])
    )
    await state.set_state(AddWish.sending_wish_url)


@router.message(AddWish.sending_wish_photo)
async def wish_photo_sent(message: Message, state: FSMContext):
    photo_id = message.photo[0].file_id

    await state.update_data(photo_id=photo_id)
    await message.answer(
        texts["add_link"],
        reply_markup=make_row_keyboard(["Не присылать", "Отменить"])
    )
    await state.set_state(AddWish.sending_wish_url)


@router.message(
    AddWish.sending_wish_url,
    F.text.lower() == "не присылать"
)
async def wish_url_not_sent(message: Message, state: FSMContext):
    await state.update_data(url=None)
    await message.answer(
        texts["confirm_add"],
        reply_markup=make_row_keyboard(['Да', 'Отменить'])
    )
    await state.set_state(AddWish.database)


@router.message(AddWish.sending_wish_url)
async def wish_url_sent(message: Message, state: FSMContext):
    await state.update_data(url=message.text)
    await message.answer(
        texts["confirm_add"],
        reply_markup=make_row_keyboard(['Да', 'Отменить'])
    )
    await state.set_state(AddWish.database)


@router.message(
    F.text.lower() == "да",
    AddWish.database
)
async def add_to_database(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    wish_data = await state.get_data()
    wish = Wishlist(
        name=wish_data['name'],
        price=wish_data['price'],
        description=wish_data['description'],
        photo_id=wish_data['photo_id'],
        url=wish_data['url'],
        user_id=user_id)

    user.wishlists.append(wish)
    session.add(user)
    session.commit()

    await message.answer(
        "Успешно добавлено!",
        reply_markup=wishlist_kb
    )
    await state.clear()


@router.message(
    F.text.lower() == "посмотреть вишлист"
)
async def view_wishlist(message: Message):
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    wishlist_text = ""
    wishlist = user.wishlists

    if len(user.wishlists) == 0:
        await message.answer(
            texts['create_wl'],
            reply_markup=make_row_keyboard(
                ["Создать Вишлист", "Отменить"])
        )

    else:
        for index, wish in enumerate(wishlist):
            if wish.price is None:
                wishlist_text += "{}) {} |  \n".format(index + 1, wish.name)

            else:
                wishlist_text += "{}) {} | {}\n".format(index + 1, wish.name, wish.price)

        await message.answer(
            texts['view_wl'].format('-' * 50, wishlist_text),
            reply_markup=make_row_keyboard(
                ["Посмотреть конкретное желание", "Меню"]
            )
        )


@router.message(
    StateFilter(None),
    F.text.lower() == 'посмотреть конкретное желание'
)
async def check_item_wl_reply(
    message: Message,
    state: FSMContext
):
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    wishlist = user.wishlists

    await state.update_data(wishlist=wishlist)
    await message.answer(
        texts["check_item_wl_reply"],
        reply_markup=make_num_keyboard(wishlist)
    )
    await state.set_state(CheckWish.choosing_item_wl)


@router.message(
    CheckWish.choosing_item_wl,
    F.text.regexp(r"^\d+$").as_("digits")
)
async def check_item_wl(message: Message, state: FSMContext):
    id = int(message.text)

    wish_data = await state.get_data()
    wishlist = wish_data['wishlist']
    wish = wishlist[id - 1]

    name = wish.name
    price = wish.price
    description = wish.description
    photo = wish.photo_id
    url = wish.url

    wish_info = "Название: {}\n".format(name)

    inline_builder = InlineKeyboardBuilder()

    if price is not None:
        wish_info += "Цена: {}\n\n".format(str(price))

    if description is not None:
        wish_info += "Описание: {}\n".format(description)

    if photo is not None:

        if url is not None:
            inline_builder.row(
                types.InlineKeyboardButton(text='Ссылка', url=url))
            await message.answer_photo(
                photo,
                caption=wish_info,
                reply_markup=inline_builder.as_markup()
            )
            await state.clear()

        else:
            await message.answer_photo(
                photo,
                caption=wish_info,
                reply_markup=menu_kb
            )
            await state.clear()

    else:
        if url is not None:
            inline_builder.row(
                types.InlineKeyboardButton(text='Ссылка', url=url))
            await message.answer(
                wish_info,
                reply_markup=inline_builder.as_markup(),
            )
            await state.clear()

        else:
            await message.answer(
                wish_info,
                reply_markup=menu_kb
            )
            await state.clear()


@router.message(
    StateFilter(None),
    F.text.lower() == "удалить из вишлиста"
)
async def delete_from_wishlist_reply(
        message: Message,
        state: FSMContext
):
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    wishlist = user.wishlists

    await view_wishlist(message)
    await state.set_state(DelWish.deleting_wish)
    await message.answer(
        texts['delete_from_wl'],
        reply_markup=make_num_keyboard(wishlist)
    )


@router.message(
    DelWish.deleting_wish,
    F.text.regexp(r"^\d+$").as_("digits")
)
async def delete_from_wishlist(
        message: Message,
        state: FSMContext
):
    id = int(message.text)
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    wish = user.wishlists[id - 1]

    if wish is not None:
        session.delete(wish)
        session.commit()
        await message.answer(
            "Успешно удалено!",
            reply_markup=wishlist_kb
        )
        await view_wishlist(message)
        await state.clear()

    else:
        await message.answer(
            "Желания под таким номером "
            "не существует!"
        )
        return


@router.message(
    StateFilter(None),
    F.text.lower() == "отменить"
)
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено!",
        reply_markup=menu_kb
    )


@router.message(
    StateFilter(None),
    F.text.lower() == "меню"
)
async def menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        texts['menu'],
        reply_markup=menu_kb
    )
