from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import dotenv_values

from states import AddFriend
from keyboard import friend_kb, menu_kb, make_row_keyboard, make_num_keyboard
from database.models import User
from texts import texts


config = dotenv_values('.env')
database_url = config['DATABASE_URL']

engine = create_engine(database_url, echo=True, pool_recycle=7200)
session = Session(engine)

router = Router()


@router.message(F.text.lower() == "друзья")
async def friends_reply(message: Message):
    await message.answer(
        texts['friends'],
        reply_markup=friend_kb
    )


@router.message(F.text.lower() == "посмотреть друзей")
async def check_friends(message: Message):
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    friends = user.get_friends(session)

    if len(friends) == 0:
        await message.answer(
            "Друзей нет!"
        )

    else:
        friend_text = ""
        for index, friend in enumerate(friends):
            friend_text += "{}) {} | {}\n".format(
                index + 1, friend.name, friend.user_id)

        await message.answer(
            texts["check_req_list"]
            .format("Друзья", '-' * 50, friend_text),
            reply_markup=make_row_keyboard([
                'Посмотреть Вишлист друга', 'Удалить', 'Отменить'
            ])
        )


@router.message(
    StateFilter(None),
    F.text.lower().in_(
        {"удалить", "удалить из друзей"}
    )
)
async def delete_friend_reply(
        message: Message,
        state: FSMContext
):
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    friends = user.get_friends(session)

    if len(friends) == 0:
        await message.answer(
            "Друзей нет!"
        )

    else:
        await check_requests(message)
        await message.answer(
            texts["delete_friend"],
            reply_markup=make_num_keyboard(friends)
        )
        await state.set_state(AddFriend.deleting_friend)


@router.message(
    AddFriend.deleting_friend,
    F.text.regexp(r"^\d+$").as_("digits")
)
async def delete_friend(message: Message, state: FSMContext):
    id = int(message.text)

    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    friends = user.get_friends(session)
    friend = friends[id - 1]

    if friend is not None:
        user.friends.remove(friend)
        session.add(user)
        session.commit()
        await message.answer(
            "{} удален из друзей!".format(friend.name),
            reply_markup=friend_kb
        )
        await state.clear()

    else:
        await message.answer(
            "Друга под таким номером "
            "не существует!"
        )
        await state.set_state(AddFriend.deleting_friend)


@router.message(
    StateFilter(None),
    F.text.lower() == "добавить в друзья"
)
async def add_friend(message: Message, state: FSMContext):
    await message.answer(
        texts["add_friend"],
        reply_markup=make_row_keyboard(['Отменить'])
    )
    await state.set_state(AddFriend.sending_contact)


@router.message(
    AddFriend.sending_contact,
    F.contact
)
async def send_request(message: Message, state: FSMContext):
    user_id = message.from_user.id
    contact_user_id = message.contact.user_id

    user = session.query(User).filter_by(
        user_id=user_id).first()

    contact_user = session.query(User).filter_by(
        user_id=contact_user_id).first()

    request = user.send_friend_request(contact_user)

    if contact_user is None:
        await message.answer(
            "Данный пользователь ещё "
            "не зарегистрировался",
            reply_markup=friend_kb
        )

    if request is None:
        await message.answer(
            "Запрос уже существует "
            "или вы уже друзья",
            reply_markup=friend_kb
        )
        await state.clear()

    else:
        session.add(request)
        session.commit()
        await message.answer(
            text="Запрос отправлен!",
            reply_markup=friend_kb
        )
        await state.clear()


@router.message(
    F.text.lower() == "посмотреть входящие заявки"
)
async def check_requests(message: Message):
    user_id = message.from_user.id
    user = session.query(User).filter_by(
        user_id=user_id).first()

    incoming_requests = user.get_incoming_requests(
        session=session)

    if len(incoming_requests) == 0:
        await message.answer(
            "Заявок нет!"
        )

    else:
        req_text = ""
        for index, req_user in enumerate(incoming_requests):
            req_text += "{}) {} | {}\n".format(
                index + 1, req_user.name, req_user.user_id)

        await message.answer(
            texts["check_req_list"]
            .format("Входящие заявки", '-' * 50, req_text),
            reply_markup=make_row_keyboard(['Принять', 'Отклонить', 'Отменить'])
        )


@router.message(
    StateFilter(None),
    F.text.lower() == "принять"
)
async def accept_request_reply(
        message: Message,
        state: FSMContext
):
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    incoming_requests = user.get_incoming_requests(
        session=session)

    await check_requests(message)
    await message.answer(
        texts["processing_request"].format("принять"),
        reply_markup=make_num_keyboard(incoming_requests)
    )
    await state.set_state(AddFriend.accepting_request)


@router.message(
    StateFilter(None),
    F.text.lower() == "отклонить"
)
async def cancel_request_reply(
        message: Message,
        state: FSMContext
):
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    incoming_requests = user.get_incoming_requests(
        session=session)

    await check_requests(message)
    await message.answer(
        texts["processing_request"].format("отклонить"),
        reply_markup=make_num_keyboard(incoming_requests)
    )
    await state.set_state(AddFriend.deleting_request)


@router.message(
    AddFriend.accepting_request,
    F.text.regexp(r"^\d+$").as_("digits")
)
async def accept_friend_request(message: Message, state: FSMContext):
    id = int(message.text)

    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    incoming_requests = user.get_incoming_requests(
        session=session)
    request_user = incoming_requests[id - 1]

    if request_user is not None and user.can_accept_request(request_user):
        user.friends.append(request_user)
        user.requests.remove(request_user)
        session.add(user)
        session.commit()

        await message.answer(
            "Заявка принята!",
            reply_markup=friend_kb
        )
        await state.clear()

    else:
        await message.answer(
            "Заявки под таким номером "
            "не существует!"
        )
        await state.set_state(AddFriend.accepting_request)


@router.message(
    AddFriend.deleting_request,
    F.text.regexp(r"^\d+$").as_("digits")
)
async def cancel_friend_request(message: Message, state: FSMContext):
    id = int(message.text)

    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    incoming_requests = user.get_incoming_requests(
        session=session)
    request_user = incoming_requests[id - 1]

    if request_user is not None and user.can_accept_request(request_user):
        user.friends.append(request_user)
        user.requests.remove(request_user)
        session.add(user)
        session.commit()

        await message.answer(
            "Заявка отклонена!",
            reply_markup=friend_kb
        )
        await state.clear()

    else:
        await message.answer(
            "Заявки под таким номером "
            "не существует!"
        )
        await state.set_state(AddFriend.deleting_request)


@router.message(
    StateFilter(None),
    F.text.lower() == 'посмотреть вишлист друга'
)
async def check_friend(message: Message, state: FSMContext):
    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    friends = user.get_friends(session)

    if len(friends) == 0:
        await message.answer(
            "Друзей нет!"
        )

    else:
        await check_friends(message)
        await message.answer(
            "Выберите номер друга, "
            "<b>Вишлист</b> которого хотите посмотреть",
            reply_markup=make_num_keyboard(friends)
        )
        await state.set_state(AddFriend.viewing_wishlist)


@router.message(
    AddFriend.viewing_wishlist,
    F.text.regexp(r"^\d+$").as_("digits")
)
async def check_friend_wishlist(message: Message, state: FSMContext):
    id = int(message.text)

    user = session.query(User).filter_by(
        user_id=message.from_user.id).first()

    friends = user.get_friends(session)
    friend = friends[id - 1]

    if friend is not None:
        friend_wishlist = friend.wishlists

        await state.update_data(friend_wishlist=friend_wishlist)

        if len(friend.wishlists) == 0:
            await message.answer(
                "У друга еще нет Вишлиста!",
                reply_markup=menu_kb
            )
            await state.clear()
            return

        else:
            wishlist_text = ""
            for index, wish in enumerate(friend_wishlist):
                if wish.price is None:
                    wishlist_text += "{}) {} |  \n".format(index + 1, wish.name)

                else:
                    wishlist_text += "{}) {} | {}\n".format(index + 1, wish.name, wish.price)

            await message.answer(
                texts['view_friend_wl'].format('-' * 50, wishlist_text),
                reply_markup=make_row_keyboard([
                    'Посмотреть конкретное желание',
                    'Меню'
                ])
            )
            await state.set_state(AddFriend.choosing_item)

    else:
        await message.answer(
            "Друга под таким номером "
            "не существует!"
        )
        await state.set_state(AddFriend.viewing_wishlist)


@router.message(
    AddFriend.choosing_item,
    F.text.lower() == 'посмотреть конкретное желание'
)
async def check_item_friend_wl_reply(
    message: Message,
    state: FSMContext
):
    wish_data = await state.get_data()
    wishlist = wish_data['friend_wishlist']

    await message.answer(
        texts["check_item_wl_reply"],
        reply_markup=make_num_keyboard(wishlist)
    )
    await state.set_state(AddFriend.viewing_item_wl)


@router.message(
    AddFriend.viewing_item_wl,
    F.text.regexp(r"^\d+$").as_("digits")
)
async def check_item_friend_wl(message: Message, state: FSMContext):
    id = int(message.text)

    wish_data = await state.get_data()
    wishlist = wish_data['friend_wishlist']
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
    F.text.lower() == "отменить"
)
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено!",
        reply_markup=menu_kb
    )
